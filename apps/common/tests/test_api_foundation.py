from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import path
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.test import APIClient
from rest_framework.views import APIView

from apps.common.pagination import StandardPageNumberPagination


class NumberSerializer(serializers.Serializer[dict[str, int]]):
    value = serializers.IntegerField()


class ValidationProbeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):  # type: ignore[no-untyped-def]
        raise serializers.ValidationError({"field": ["invalid"]})


class NumberListView(ListAPIView):  # type: ignore[type-arg]
    permission_classes = [AllowAny]
    serializer_class = NumberSerializer
    pagination_class = StandardPageNumberPagination

    def get_queryset(self):  # type: ignore[no-untyped-def]
        return [{"value": value} for value in range(3)]


urlpatterns = [
    path("probe/error", ValidationProbeView.as_view()),
    path("probe/numbers", NumberListView.as_view()),
]


class RequestIDTests(SimpleTestCase):
    def test_response_includes_supplied_request_id(self) -> None:
        response = self.client.get("/health", headers={"X-Request-ID": "req-123"})

        self.assertEqual(response["X-Request-ID"], "req-123")

    def test_response_generates_request_id_when_missing(self) -> None:
        response = self.client.get("/health")

        self.assertTrue(response["X-Request-ID"])


@override_settings(ROOT_URLCONF=__name__)
class CommonAPIContractTests(SimpleTestCase):
    def test_error_response_uses_common_contract(self) -> None:
        response = self.client.get("/probe/error", headers={"X-Request-ID": "req-err"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "code": "invalid",
                "message": "Validation failed.",
                "details": {"field": ["invalid"]},
                "request_id": "req-err",
            },
        )

    def test_pagination_uses_shared_contract(self) -> None:
        response = self.client.get("/probe/numbers?page_size=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 3)
        self.assertEqual(response.json()["results"], [{"value": 0}, {"value": 1}])


class AdminRESTAuthTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user_model = get_user_model()

    def test_admin_endpoint_rejects_anonymous_users(self) -> None:
        response = self.client.get("/api/v1/admin/session")

        self.assertEqual(response.status_code, 403)

    def test_admin_endpoint_rejects_non_staff_users(self) -> None:
        user = self.user_model.objects.create_user("user@example.com")
        self.client.force_login(user)

        response = self.client.get("/api/v1/admin/session")

        self.assertEqual(response.status_code, 403)

    def test_admin_endpoint_accepts_staff_users(self) -> None:
        staff = self.user_model.objects.create_user(
            "staff@example.com",
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.get("/api/v1/admin/session")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"email": "staff@example.com", "is_staff": True},
        )
