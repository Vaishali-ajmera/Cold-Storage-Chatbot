from django.urls import path

from chat.views import (
    AnswerMCQView,
    AskQuestionView,
    ChatHistoryView,
    CreateSessionView,
    DailyQuotaStatusView,
    GetSessionIntakeView,
    ListUserSessionsAPIView,
    TaskStatusView,
    UpdateSessionTitleAPIView,
)

urlpatterns = [
    path("ask/", AskQuestionView.as_view(), name="ask-question"),
    path("mcq-response/", AnswerMCQView.as_view(), name="mcq-response"),
    
    path("task/<str:task_id>/status/", TaskStatusView.as_view(), name="task-status"),
    
    path("history/<uuid:session_id>/", ChatHistoryView.as_view(), name="chat-history"),
    path("sessions/", ListUserSessionsAPIView.as_view(), name="list-sessions"),
    path("sessions/create/", CreateSessionView.as_view(), name="create-session"),
    path(
        "sessions/<uuid:session_id>/title/",
        UpdateSessionTitleAPIView.as_view(),
        name="update-session-title",
    ),
    path(
        "sessions/<uuid:session_id>/intake/",
        GetSessionIntakeView.as_view(),
        name="get-session-intake",
    ),
    path("quota/", DailyQuotaStatusView.as_view(), name="daily-quota-status"),
]
