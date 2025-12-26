from django.urls import path

from usecase_engine.views import UserInputAPIView

urlpatterns = [
    path("intake/", UserInputAPIView.as_view(), name="intake-list"),
]
