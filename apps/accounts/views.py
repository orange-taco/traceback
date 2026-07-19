from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_session_status(request: Request) -> Response:
    email = getattr(request.user, "email", "")
    return Response(
        {
            "email": email,
            "is_staff": request.user.is_staff,
        }
    )
