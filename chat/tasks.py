import logging

from celery import shared_task

from chat.constants import (
    MESSAGE_TYPE_USER_QUESTION,
    SENDER_USER,
    SESSION_ACTIVE,
)

logger = logging.getLogger("chat.tasks")


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def process_question_task(
    self,
    session_id: str,
    question: str,
    intake_data: dict,
    user_id: int,
) -> dict:
    from chat.models import ChatMessage, ChatSession, DailyQuestionQuota
    from chat.services import ChatService

    try:
        logger.info(f"[TASK] Processing question for session {session_id}")

        session = ChatSession.objects.select_related("user").get(id=session_id)

        if session.user_id != user_id:
            return {
                "success": False,
                "error": "Unauthorized access to session",
            }

        # Check if session is active
        if not session.is_active():
            return {
                "success": False,
                "error": "This session is no longer active. Please start a new chat to continue.",
            }

        # Check daily quota
        daily_quota = DailyQuestionQuota.get_or_create_today(session.user)
        if not daily_quota.can_ask_question():
            from chat.models import get_max_daily_questions
            max_questions = get_max_daily_questions()
            return {
                "success": False,
                "error": f"You've reached your daily limit of {max_questions} questions. Please try again tomorrow.",
                "daily_limit_reached": True,
            }

        if not session.title:
            session.set_title_from_question(question)

        chat_service = ChatService(session)

        response_data = chat_service.process_user_question(question, intake_data)

        logger.info(f"[TASK] Successfully processed question for session {session_id}")

        return {
            "success": True,
            "session_id": str(session.id),
            "type": response_data.get("type"),
            "response_message": response_data.get("message"),
            "suggestions": response_data.get("suggestions"),
            "mcq": response_data.get("mcq"),
            "mcq_message_id": response_data.get("mcq_message_id"),
            "remaining_daily_questions": daily_quota.remaining_questions(),
        }

    except ChatSession.DoesNotExist:
        logger.error(f"[TASK] Session not found: {session_id}")
        return {
            "success": False,
            "error": "Session not found",
        }

    except Exception as e:
        logger.error(f"[TASK] Error processing question: {str(e)}", exc_info=True)

        error_str = str(e).lower()
        if any(x in error_str for x in ["timeout", "connection", "500"]):
            raise self.retry(exc=e)

        return {
            "success": False,
            "error": f"Failed to process question: {str(e)}",
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def process_mcq_response_task(
    self,
    session_id: str,
    mcq_message_id: str,
    selected_value: str,
    intake_data: dict,
    user_id: int,
) -> dict:
    from chat.models import ChatMessage, ChatSession, DailyQuestionQuota
    from chat.services import ChatService

    try:
        logger.info(f"[TASK] Processing MCQ response for session {session_id}")

        session = ChatSession.objects.select_related("user").get(id=session_id)

        if session.user_id != user_id:
            return {
                "success": False,
                "error": "Unauthorized access to session",
            }

        try:
            mcq_message = ChatMessage.objects.get(id=mcq_message_id, session=session)
        except ChatMessage.DoesNotExist:
            return {
                "success": False,
                "error": "MCQ message not found",
            }

        chat_service = ChatService(session)

        response_data = chat_service.process_mcq_response(
            mcq_message_id,
            selected_value,
            intake_data,
        )

        # Get daily quota for response
        daily_quota = DailyQuestionQuota.get_or_create_today(session.user)

        logger.info(
            f"[TASK] Successfully processed MCQ response for session {session_id}"
        )

        return {
            "success": True,
            "session_id": str(session.id),
            "type": response_data.get("type"),
            "response_message": response_data.get("message"),
            "suggestions": response_data.get("suggestions"),
            "mcq": response_data.get("mcq"),
            "mcq_message_id": response_data.get("mcq_message_id"),
            "remaining_daily_questions": daily_quota.remaining_questions(),
        }

    except ChatSession.DoesNotExist:
        logger.error(f"[TASK] Session not found: {session_id}")
        return {
            "success": False,
            "error": "Session not found",
        }

    except Exception as e:
        logger.error(f"[TASK] Error processing MCQ response: {str(e)}", exc_info=True)

        error_str = str(e).lower()
        if any(x in error_str for x in ["timeout", "connection", "500"]):
            raise self.retry(exc=e)

        return {
            "success": False,
            "error": f"Failed to process MCQ response: {str(e)}",
        }
