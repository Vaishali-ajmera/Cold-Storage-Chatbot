from django.urls import path

from usecase_engine.views import (
    GeminiAdvisoryAPI,
    SuggestedRelatedAPIView,
    UserInputAPIView,
    UserInputDetailAPIView,
)

urlpatterns = [
    path("intake/", UserInputAPIView.as_view(), name="intake-list"),
    path("intake/<int:pk>/", UserInputDetailAPIView.as_view(), name="intake-detail"),
    path(
        "suggested-related/",
        SuggestedRelatedAPIView.as_view(),
        name="suggested-related",
    ),
    path("ask-gemini/", GeminiAdvisoryAPI.as_view(), name="ask-gemini"),
]
