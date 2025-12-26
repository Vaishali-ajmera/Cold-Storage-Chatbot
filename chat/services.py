import json

import openai
from django.conf import settings
from django.db import transaction

from chat.constants import (
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
    get_rejection_message,
)

# Initialize OpenAI
openai.api_key = settings.OPENAI_API_KEY


class ChatService:
    def __init__(self, session):
        self.session = session

    def call_openai(self, system_prompt, user_prompt, temperature=0.3):
        """
        Call OpenAI API with error handling
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",  # or gpt-3.5-turbo for cheaper
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},  # Force JSON output
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            # Log error
            print(f"OpenAI API Error: {str(e)}")
            raise

    @transaction.atomic
    def process_user_question(self, question_text, intake_data, chat_history):
        """
        Process user question through 3-prompt flow
        
        Args:
            question_text: The user's question
            intake_data: Dict with 'user_choice' and 'intake_data' from DB
            chat_history: List of previous messages
        """
        # Save user's question
        user_message = ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_USER,
            message_text=question_text,
            message_type=MESSAGE_TYPE_USER_QUESTION,
        )

        # Increment question counter
        self.session.increment_question_count()

        # STEP 1: Call Classifier Prompt
        system_prompt, user_prompt = get_classifier_prompt(
            intake_data, chat_history, question_text
        )

        classification = self.call_openai(system_prompt, user_prompt)

        # Handle based on classification
        if classification["classification"] == "OUT_OF_CONTEXT":
            return self._handle_out_of_context()

        elif classification["classification"] == "NEEDS_FOLLOW_UP":
            return self._handle_needs_followup(
                question_text, classification["missing_field"], intake_data
            )

        else:  # ANSWER_DIRECTLY
            return self._handle_direct_answer(question_text, intake_data, chat_history)

    def _handle_out_of_context(self):
        """Handle out-of-context questions"""
        rejection = get_rejection_message()

        # Save bot's rejection
        ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_BOT,
            message_text=rejection["message"],
            message_type=MESSAGE_TYPE_BOT_REJECTION,
            suggested_questions={"questions": rejection["suggested_questions"]},
        )

        # Decrement counter (out-of-context doesn't count)
        self.session.user_questions_count -= 1
        self.session.save()

        return {
            "type": "rejection",
            "message": rejection["message"],
            "suggestions": rejection["suggested_questions"],
            "remaining_questions": self.session.remaining_questions(),
        }

    def _handle_needs_followup(self, original_question, missing_field, intake_data):
        """Generate MCQ to collect missing info"""
        # STEP 2: Call MCQ Generator Prompt
        system_prompt, user_prompt = get_mcq_generator_prompt(
            intake_data, original_question, missing_field
        )

        mcq_data = self.call_openai(system_prompt, user_prompt)

        # Save bot's MCQ question
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

    def _handle_direct_answer(self, question_text, intake_data, chat_history, mcq_response=None):
        """Generate final answer"""
        # STEP 3: Call Answer Generator Prompt
        system_prompt, user_prompt = get_answer_generator_prompt(
            intake_data, chat_history, question_text, mcq_response
        )

        answer_data = self.call_openai(system_prompt, user_prompt, temperature=0.7)

        # Save bot's answer
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
    def process_mcq_response(self, mcq_message_id, selected_option, selected_value, intake_data, chat_history):
        """
        Handle user's MCQ response and generate final answer
        
        Args:
            mcq_message_id: UUID of the MCQ question message
            selected_option: Selected option key (A, B, C, D)
            selected_value: Full text of selected option
            intake_data: Dict with 'user_choice' and 'intake_data' from DB
            chat_history: List of previous messages
        """

        # Get the MCQ message
        mcq_message = ChatMessage.objects.get(id=mcq_message_id)

        # Save user's MCQ response
        ChatMessage.objects.create(
            session=self.session,
            sender=SENDER_USER,
            message_text=selected_value,
            message_type=MESSAGE_TYPE_USER_MCQ,
            mcq_selected_option=selected_option,
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

        # Generate answer with MCQ context
        return self._handle_direct_answer(
            original_question, 
            intake_data, 
            chat_history,
            mcq_response=f"User selected: {selected_value}"
        )
