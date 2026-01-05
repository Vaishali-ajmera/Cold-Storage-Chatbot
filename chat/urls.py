from django.urls import path

from chat.views import (
    AnswerMCQView,
    AskQuestionView,
    ChatHistoryView,
    ListUserSessionsAPIView,
    UpdateSessionTitleAPIView,
)

urlpatterns = [
    path("ask/", AskQuestionView.as_view(), name="ask-question"),
    path("mcq-response/", AnswerMCQView.as_view(), name="mcq-response"),
    path("history/<uuid:session_id>/", ChatHistoryView.as_view(), name="chat-history"),
    path("sessions/", ListUserSessionsAPIView.as_view(), name="list-sessions"),
    path(
        "sessions/<uuid:session_id>/title/",
        UpdateSessionTitleAPIView.as_view(),
        name="update-session-title",
    ),
]
