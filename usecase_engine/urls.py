from django.urls import path

from usecase_engine.views import UseCaseListView, WizardQuestionsView

urlpatterns = [
    path("usecases/", UseCaseListView.as_view(), name="usecase-list"),
    path("wizard/questions/", WizardQuestionsView.as_view(), name="wizard-questions"),
]
