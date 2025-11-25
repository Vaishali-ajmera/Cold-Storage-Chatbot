from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from usecase_engine.constants import USE_CASES
from usecase_engine.knowledge_base import QUESTION_BANK


class UseCaseListView(APIView):

    def get(self, request):
        try:
            return Response(
                {
                    "message": "Usecase list fetched successfully",
                    "data": USE_CASES,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"message": f"Unexpected error fetching usecases: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WizardQuestionsView(APIView):

    def get(self, request):
        try:
            
            usecase = request.query_params.get("usecase")
            
            if not usecase:
                return Response(
                    {"message": "Query parameter 'usecase' is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            valid_usecases = [uc["id"] for uc in USE_CASES]            

            if usecase not in valid_usecases:
                return Response(
                    {
                        "message": (
                            f"Invalid usecase '{usecase}'. "
                            f"Valid options: {', '.join(valid_usecases)}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            general_context = QUESTION_BANK["general_context"]            
            usecase_data = QUESTION_BANK["usecase_sections"].get(usecase)

            if not usecase_data:
                return Response(
                    {"message": f"No question-set found for usecase '{usecase}'"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            usecase_sections = usecase_data.get("sections", [])

            return Response(
                {
                    "message": "Wizard questions fetched successfully",
                    "data": {
                        "usecase": usecase,
                        "general": {
                            "title": general_context.get("title", ""),
                            "description": general_context.get("description", ""),
                            "questions": general_context.get("questions", []),
                        },
                        "usecase_specific": {
                            "title": usecase_data.get("title", ""),
                            "description": usecase_data.get("description", ""),
                            "sections": usecase_sections,
                        },
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"message": f"Unexpected server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
