import json
import logging
import time

from decouple import config
from django.db import transaction
from google import genai
from google.genai import types

from chat.constants import (
    LLM_MODEL_NAME,
    MESSAGE_TYPE_BOT_ANSWER,
    MESSAGE_TYPE_BOT_MCQ,
    MESSAGE_TYPE_BOT_REJECTION,
    MESSAGE_TYPE_USER_MCQ,
    MESSAGE_TYPE_USER_QUESTION,
    SENDER_BOT,
    SENDER_USER,
)
from chat.models import ChatMessage, ChatSession, DailyQuestionQuota
from chat.prompts import (
    get_answer_generator_prompt,
    get_classifier_prompt,
    get_mcq_generator_prompt,
    get_meta_response_prompt,
    get_out_of_context_response_prompt,
)

# Simple logger setup
logger = logging.getLogger("chat.service")


class ChatService:

    def __init__(self, session: ChatSession):
        from accounts.constants import LANGUAGE_MAP

        self.session = session
        self.user_language_code = session.user.preferred_language
        self.user_language_full = LANGUAGE_MAP.get(self.user_language_code, "English")

    def call_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        purpose: str = "unknown",
    ) -> dict:
        api_key = config("GEMINI_API_KEY", default=None)

        if not api_key:
            raise Exception("GEMINI_API_KEY not configured in environment")

        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model=LLM_MODEL_NAME,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        response_mime_type="application/json",
                    ),
                    contents=user_prompt,
                )

                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage = response.usage_metadata
                    prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
                    candidates_tokens = getattr(usage, "candidates_token_count", 0) or 0
                    thoughts_tokens = getattr(usage, "thoughts_token_count", 0) or 0
                    total_tokens = getattr(usage, "total_token_count", 0) or 0

                    logger.info(
                        f"[{purpose}] Token Usage:\n"
                        f"   ├─ Prompt (input):    {prompt_tokens:,} tokens\n"
                        f"   ├─ Response (output): {candidates_tokens:,} tokens\n"
                        f"   ├─ Thinking:          {thoughts_tokens:,} tokens\n"
                        f"   └─ Total:             {total_tokens:,} tokens"
                    )

                result = json.loads(response.text)
                return result

            except json.JSONDecodeError as e:
                last_error = e
                logger.error(
                    f"[{purpose}] JSON Parse Error (attempt {attempt}/{max_retries}):\n"
                    f"   ├─ Error: {str(e)}\n"
                    f"   └─ Raw Response: {response.text[:500] if hasattr(response, 'text') else 'N/A'}..."
                )
                if attempt < max_retries:
                    time.sleep(1 * attempt)
                    continue

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check if it's a quota/rate limit error - DON'T retry these
                if (
                    "429" in error_str
                    or "quota" in error_str
                    or "resource_exhausted" in error_str
                ):
                    logger.error(
                        f"[{purpose}] Quota Exceeded - NOT retrying:\n"
                        f"   ├─ Type: {type(e).__name__}\n"
                        f"   └─ Message: {str(e)[:200]}..."
                    )
                    raise e  # Fail immediately, no retry

                logger.error(
                    f"[{purpose}] API Error (attempt {attempt}/{max_retries}):\n"
                    f"   ├─ Type: {type(e).__name__}\n"
                    f"   └─ Message: {str(e)}"
                )

                # Retry on timeout or 500 errors
                if any(x in error_str for x in ["timeout", "500"]):
                    if attempt < max_retries:
                        time.sleep(2**attempt)
                        continue

                # For other errors, don't retry
                break

        logger.error(
            f"[{purpose}] All retries exhausted. Final error: {type(last_error).__name__}: {str(last_error)}"
        )
        raise last_error

    @transaction.atomic
    def process_user_question(self, question_text: str, intake_data: dict) -> dict:
        logger.info(
            f"📝 User prompt: {question_text[:100]}{'...' if len(question_text) > 100 else ''}"
        )

        ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_USER,
            message_text=question_text,
            message_type=MESSAGE_TYPE_USER_QUESTION,
        )

        # Note: Daily quota is already checked and incremented in views/tasks
        # No need to increment here

        llm_context = self.session.get_llm_context()

        system_prompt, user_prompt = get_classifier_prompt(
            intake_data, llm_context, question_text
        )

        classification = self.call_gemini(
            system_prompt,
            user_prompt,
            temperature=0.3,
            purpose="CLASSIFIER",
        )

        classification_result = classification.get("classification", "ANSWER_DIRECTLY")

        logger.info(f"🔍 Classifier result: {classification_result}")

        if classification_result == "META":
            result = self._handle_meta_question(
                question_text, classification.get("meta_subtype", "identity")
            )

        elif classification_result == "OUT_OF_CONTEXT":
            result = self._handle_out_of_context(
                question_text, classification.get("out_of_context_type", "unrelated")
            )

        elif classification_result == "NEEDS_FOLLOW_UP":
            missing_field = classification.get("missing_field", "unknown")
            result = self._handle_needs_followup(
                question_text, missing_field, intake_data, llm_context
            )

        else:  # ANSWER_DIRECTLY
            result = self._handle_direct_answer(question_text, intake_data, llm_context)

        return result

    def _handle_meta_question(self, question_text: str, meta_subtype: str) -> dict:
        system_prompt, user_prompt = get_meta_response_prompt(
            question_text, meta_subtype, self.user_language_full
        )

        meta_response = self.call_gemini(
            system_prompt,
            user_prompt,
            temperature=0.7,
            purpose="META_RESPONSE",
        )

        ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_BOT,
            message_text=meta_response["answer"],
            message_type=MESSAGE_TYPE_BOT_ANSWER,
            suggested_questions=None,
        )

        # Get daily quota for remaining questions
        daily_quota = DailyQuestionQuota.get_or_create_today(self.session.user)

        return {
            "type": "meta",
            "message": meta_response["answer"],
            "suggestions": [],
            "remaining_daily_questions": daily_quota.remaining_questions(),
        }

    def _handle_out_of_context(
        self, question_text: str, out_of_context_type: str
    ) -> dict:
        system_prompt, user_prompt = get_out_of_context_response_prompt(
            question_text, out_of_context_type, self.user_language_full
        )

        redirect_response = self.call_gemini(
            system_prompt,
            user_prompt,
            temperature=0.7,
            purpose="OUT_OF_CONTEXT_RESPONSE",
        )

        ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_BOT,
            message_text=redirect_response["answer"],
            message_type=MESSAGE_TYPE_BOT_REJECTION,
            suggested_questions=None,
        )

        # Get daily quota for remaining questions
        daily_quota = DailyQuestionQuota.get_or_create_today(self.session.user)

        return {
            "type": "rejection",
            "message": redirect_response["answer"],
            "suggestions": [],
            "remaining_daily_questions": daily_quota.remaining_questions(),
        }

    def _handle_needs_followup(
        self,
        original_question: str,
        missing_field: str,
        intake_data: dict,
        llm_context: list,
    ) -> dict:
        system_prompt, user_prompt = get_mcq_generator_prompt(
            intake_data, original_question, missing_field, self.user_language_full
        )

        mcq_data = self.call_gemini(
            system_prompt,
            user_prompt,
            temperature=0.3,
            purpose="MCQ_GENERATOR",
        )

        mcq_message = ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_BOT,
            message_text=f"To answer your question, I need: {mcq_data['question']}",
            message_type=MESSAGE_TYPE_BOT_MCQ,
            mcq_options=mcq_data,
        )

        self.session.append_to_llm_context(SENDER_USER, original_question)

        # Get daily quota for remaining questions
        daily_quota = DailyQuestionQuota.get_or_create_today(self.session.user)

        return {
            "type": "mcq",
            "message": "To answer your question, I need:",
            "mcq": mcq_data,
            "mcq_message_id": str(mcq_message.id),
            "remaining_daily_questions": daily_quota.remaining_questions(),
        }

    def _handle_direct_answer(
        self,
        question_text: str,
        intake_data: dict,
        llm_context: list,
        mcq_response: str = None,
    ) -> dict:
        system_prompt, user_prompt = get_answer_generator_prompt(
            intake_data,
            llm_context,
            question_text,
            self.user_language_full,
            mcq_response,
        )

        answer_data = self.call_gemini(
            system_prompt,
            user_prompt,
            temperature=0.7,
            purpose="ANSWER_GENERATOR",
        )

        ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_BOT,
            message_text=answer_data["answer"],
            message_type=MESSAGE_TYPE_BOT_ANSWER,
            suggested_questions={"questions": answer_data["suggested_questions"]},
        )

        if not mcq_response:
            self.session.append_to_llm_context(SENDER_USER, question_text)
        self.session.append_to_llm_context(SENDER_BOT, answer_data["answer"])

        # Get daily quota for remaining questions
        daily_quota = DailyQuestionQuota.get_or_create_today(self.session.user)

        return {
            "type": "answer",
            "message": answer_data["answer"],
            "suggestions": answer_data["suggested_questions"],
            "remaining_daily_questions": daily_quota.remaining_questions(),
        }

    @transaction.atomic
    def process_mcq_response(
        self, mcq_message_id: str, selected_value: str, intake_data: dict
    ) -> dict:
        logger.info(f"📝 User MCQ selection: {selected_value}")

        mcq_message = ChatMessage.objects.get(id=mcq_message_id)

        ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_USER,
            message_text=selected_value,
            message_type=MESSAGE_TYPE_USER_MCQ,
            parent_message=mcq_message,
        )

        original_question_msg = ChatMessage.objects.filter(
            session=self.session,
            sender=SENDER_USER,
            message_type=MESSAGE_TYPE_USER_QUESTION,
            sequence_number__lt=mcq_message.sequence_number,
        ).last()

        original_question = (
            original_question_msg.message_text
            if original_question_msg
            else "Previous question"
        )

        llm_context = self.session.get_llm_context()

        result = self._handle_direct_answer(
            original_question,
            intake_data,
            llm_context,
            mcq_response=f"User selected: {selected_value}",
        )

        return result
