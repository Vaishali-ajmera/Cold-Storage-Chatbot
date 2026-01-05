import json

from decouple import config
from django.db import transaction
from google import genai
from google.genai import types

from chat.constants import (
    CHAT_OUT_OF_CONTEXT_MESSAGE,
    MESSAGE_TYPE_BOT_ANSWER,
    MESSAGE_TYPE_BOT_MCQ,
    MESSAGE_TYPE_BOT_REJECTION,
    MESSAGE_TYPE_USER_MCQ,
    MESSAGE_TYPE_USER_QUESTION,
    SENDER_BOT,
    SENDER_USER,
)
from chat.models import ChatMessage, ChatSession
from chat.prompts import (
    get_answer_generator_prompt,
    get_classifier_prompt,
    get_mcq_generator_prompt,
)


class ChatService:
    def __init__(self, session):
        self.session = session

    def call_gemini(self, system_prompt, user_prompt, temperature=0.3):
        api_key = config("GEMINI_API_KEY", default=None)

        if not api_key:
            raise Exception("GEMINI_API_KEY not configured in environment")

        try:
            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
                contents=user_prompt,
            )

            result = json.loads(response.text)
            return result

        except Exception as e:
            # Log error
            print(f"Gemini API Error: {str(e)}")
            raise

    @transaction.atomic
    def process_user_question(self, question_text, intake_data, chat_history):

        user_message = ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_USER,
            message_text=question_text,
            message_type=MESSAGE_TYPE_USER_QUESTION,
        )

        self.session.increment_question_count()

        system_prompt, user_prompt = get_classifier_prompt(
            intake_data, chat_history, question_text
        )

        classification = self.call_gemini(system_prompt, user_prompt)

        if classification["classification"] == "OUT_OF_CONTEXT":
            return self._handle_out_of_context()

        elif classification["classification"] == "NEEDS_FOLLOW_UP":
            return self._handle_needs_followup(
                question_text, classification["missing_field"], intake_data
            )

        else:  # ANSWER_DIRECTLY
            return self._handle_direct_answer(question_text, intake_data, chat_history)

    def _handle_out_of_context(self):
        rejection = CHAT_OUT_OF_CONTEXT_MESSAGE

        ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_BOT,
            message_text=rejection["message"],
            message_type=MESSAGE_TYPE_BOT_REJECTION,
        )

        self.session.save()

        return {
            "type": "rejection",
            "message": rejection["message"],
            "remaining_questions": self.session.remaining_questions(),
        }

    def _handle_needs_followup(self, original_question, missing_field, intake_data):
        system_prompt, user_prompt = get_mcq_generator_prompt(
            intake_data, original_question, missing_field
        )

        mcq_data = self.call_gemini(system_prompt, user_prompt)

        mcq_message = ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_BOT,
            message_text=f"To answer your question, I need: {mcq_data['question']}",
            message_type=MESSAGE_TYPE_BOT_MCQ,
            mcq_options=mcq_data,
        )

        return {
            "type": "mcq",
            "message": f"To answer your question, I need:",
            "mcq": mcq_data,
            "mcq_message_id": str(mcq_message.id),
            "remaining_questions": self.session.remaining_questions(),
        }

    def _handle_direct_answer(
        self, question_text, intake_data, chat_history, mcq_response=None
    ):
        system_prompt, user_prompt = get_answer_generator_prompt(
            intake_data, chat_history, question_text, mcq_response
        )

        answer_data = self.call_gemini(system_prompt, user_prompt, temperature=0.7)

        ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_BOT,
            message_text=answer_data["answer"],
            message_type=MESSAGE_TYPE_BOT_ANSWER,
            suggested_questions={"questions": answer_data["suggested_questions"]},
        )

        return {
            "type": "answer",
            "message": answer_data["answer"],
            "suggestions": answer_data["suggested_questions"],
            "remaining_questions": self.session.remaining_questions(),
        }

    @transaction.atomic
    def process_mcq_response(
        self, mcq_message_id, selected_value, intake_data, chat_history
    ):
        mcq_message = ChatMessage.objects.get(id=mcq_message_id)

        ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_USER,
            message_text=selected_value,
            message_type=MESSAGE_TYPE_USER_MCQ,
            parent_message=mcq_message,
        )

        # Find original question (the user question before MCQ)
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

        return self._handle_direct_answer(
            original_question,
            intake_data,
            chat_history,
            mcq_response=f"User selected: {selected_value}",
        )
