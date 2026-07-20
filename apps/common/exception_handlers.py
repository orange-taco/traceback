from __future__ import annotations

from typing import Any

from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(
    exc: Exception,
    context: dict[str, Any],
) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None

    request = context.get("request")
    request_id = getattr(request, "request_id", "") if request is not None else ""
    code = _get_error_code(exc, response.status_code)
    message, details = _split_error_payload(response.data)
    response.data = {
        "code": code,
        "message": message,
        "details": details,
        "request_id": request_id,
    }
    return response


def _get_error_code(exc: Exception, status_code: int) -> str:
    if isinstance(exc, exceptions.APIException):
        code = exc.get_codes()
        if isinstance(code, str):
            return code
        if status_code == status.HTTP_400_BAD_REQUEST:
            return "invalid"
    if isinstance(exc, Http404):
        return "not_found"
    return {
        status.HTTP_400_BAD_REQUEST: "bad_request",
        status.HTTP_401_UNAUTHORIZED: "not_authenticated",
        status.HTTP_403_FORBIDDEN: "permission_denied",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
        status.HTTP_409_CONFLICT: "conflict",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "server_error",
    }.get(status_code, "error")


def _split_error_payload(data: Any) -> tuple[str, Any]:
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        return str(data["detail"]), {}
    if isinstance(data, list):
        return "Validation failed.", {"non_field_errors": data}
    if isinstance(data, dict):
        return "Validation failed.", data
    return str(data), {}
