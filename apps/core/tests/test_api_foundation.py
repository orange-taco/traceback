from __future__ import annotations

from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import path
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.core.pagination import StandardPageNumberPagination


class NumberSerializer(serializers.Serializer[dict[str, int]]):
    value = serializers.IntegerField()


class ValidationProbeView(GenericAPIView[Any]):
    permission_classes = [AllowAny]

    def get(self, request):  # type: ignore[no-untyped-def]
        raise serializers.ValidationError({"field": ["invalid"]})


class DetailValidationProbeView(GenericAPIView[Any]):
    permission_classes = [AllowAny]

    def get(self, request):  # type: ignore[no-untyped-def]
        raise serializers.ValidationError({"detail": ["required"]})


class NumberListView(GenericAPIView[Any]):
    permission_classes = [AllowAny]
    pagination_class = StandardPageNumberPagination

    def get(self, request):  # type: ignore[no-untyped-def]
        data = [{"value": value} for value in range(3)]
        paginator = self.pagination_class()
        page: Any = paginator.paginate_queryset(cast(Any, data), request, view=self)
        serializer = NumberSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class StaffProbeView(GenericAPIView[Any]):
    permission_classes = [IsAdminUser]

    def get(self, request):  # type: ignore[no-untyped-def]
        return Response({"ok": True})


urlpatterns = [
    path("probe/error", ValidationProbeView.as_view()),
    path("probe/detail-error", DetailValidationProbeView.as_view()),
    path("probe/numbers", NumberListView.as_view()),
    path("probe/staff", StaffProbeView.as_view()),
]


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

    def test_detail_field_validation_error_preserves_field_name(self) -> None:
        response = self.client.get("/probe/detail-error")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Validation failed.")
        self.assertEqual(response.json()["details"], {"detail": ["required"]})

    def test_pagination_uses_shared_contract(self) -> None:
        response = self.client.get("/probe/numbers?page_size=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 3)
        self.assertEqual(response.json()["results"], [{"value": 0}, {"value": 1}])


@override_settings(ROOT_URLCONF=__name__)
class StaffRESTAuthTests(TestCase):
    def setUp(self) -> None:
        self.api_client = APIClient()
        self.user_model = get_user_model()

    def test_staff_endpoint_rejects_anonymous_users(self) -> None:
        response = self.api_client.get("/probe/staff")

        self.assertEqual(response.status_code, 403)

    def test_staff_endpoint_rejects_non_staff_users(self) -> None:
        user = self.user_model.objects.create_user("user@example.com")
        self.api_client.force_login(user)

        response = self.api_client.get("/probe/staff")

        self.assertEqual(response.status_code, 403)

    def test_staff_endpoint_accepts_staff_users(self) -> None:
        staff = self.user_model.objects.create_user(
            "staff@example.com",
            is_staff=True,
        )
        self.api_client.force_login(staff)

        response = self.api_client.get("/probe/staff")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"ok": True},
        )
