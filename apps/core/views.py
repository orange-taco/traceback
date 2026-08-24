from django.http import JsonResponse


def health_check(request):  # type: ignore[no-untyped-def]
    return JsonResponse({"status": "ok"})
