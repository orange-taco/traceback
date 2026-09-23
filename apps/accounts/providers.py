from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings


class KakaoUnlinkError(Exception):
    pass


def unlink_kakao_user(uid: str) -> None:
    admin_key = getattr(settings, "KAKAO_ADMIN_KEY", "")
    if not admin_key:
        raise KakaoUnlinkError("KAKAO_ADMIN_KEY is not configured.")

    request = urllib.request.Request(
        "https://kapi.kakao.com/v1/user/unlink",
        data=urllib.parse.urlencode(
            {"target_id_type": "user_id", "target_id": uid}
        ).encode(),
        headers={
            "Authorization": f"KakaoAK {admin_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode() or "{}")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        raise KakaoUnlinkError("Kakao unlink request failed.") from exc

    if str(payload.get("id")) != str(uid):
        raise KakaoUnlinkError("Kakao unlink response did not match the user.")
