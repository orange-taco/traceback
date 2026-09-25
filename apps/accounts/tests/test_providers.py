from __future__ import annotations

import json
from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase, override_settings

from apps.accounts.providers import KakaoUnlinkError, unlink_kakao_user


class KakaoProviderTests(SimpleTestCase):
    @override_settings(KAKAO_ADMIN_KEY="admin-key")
    @patch("apps.accounts.providers.urllib.request.urlopen")
    def test_unlink_sends_admin_key_and_user_id(self, urlopen: Mock) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps({"id": 5047590774}).encode()
        response.__enter__.return_value = response
        urlopen.return_value = response

        unlink_kakao_user("5047590774")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://kapi.kakao.com/v1/user/unlink")
        self.assertEqual(request.get_header("Authorization"), "KakaoAK admin-key")
        self.assertEqual(
            request.data.decode(), "target_id_type=user_id&target_id=5047590774"
        )

    @override_settings(KAKAO_ADMIN_KEY="")
    def test_unlink_requires_admin_key(self) -> None:
        with self.assertRaisesRegex(KakaoUnlinkError, "not configured"):
            unlink_kakao_user("5047590774")

    @override_settings(KAKAO_ADMIN_KEY="admin-key")
    @patch("apps.accounts.providers.urllib.request.urlopen")
    def test_unlink_rejects_unexpected_user_id(self, urlopen: Mock) -> None:
        response = MagicMock()
        response.read.return_value = b'{"id": 999}'
        response.__enter__.return_value = response
        urlopen.return_value = response

        with self.assertRaisesRegex(KakaoUnlinkError, "did not match"):
            unlink_kakao_user("5047590774")

    @override_settings(KAKAO_ADMIN_KEY="admin-key")
    @patch("apps.accounts.providers.urllib.request.urlopen")
    def test_unlink_rejects_non_object_json_payload(self, urlopen: Mock) -> None:
        response = MagicMock()
        response.read.return_value = b"[]"
        response.__enter__.return_value = response
        urlopen.return_value = response

        with self.assertRaisesRegex(KakaoUnlinkError, "did not match"):
            unlink_kakao_user("5047590774")

    @override_settings(KAKAO_ADMIN_KEY="admin-key")
    @patch("apps.accounts.providers.urllib.request.urlopen")
    def test_unlink_converts_response_read_errors(self, urlopen: Mock) -> None:
        response = MagicMock()
        response.read.side_effect = TimeoutError("timed out")
        response.__enter__.return_value = response
        urlopen.return_value = response

        with self.assertRaisesRegex(KakaoUnlinkError, "request failed"):
            unlink_kakao_user("5047590774")
