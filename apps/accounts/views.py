from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class AdminSessionStatusView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request) -> Response:
        email = getattr(request.user, "email", "")
        return Response(
            {
                "email": email,
                "is_staff": request.user.is_staff,
            }
        )
