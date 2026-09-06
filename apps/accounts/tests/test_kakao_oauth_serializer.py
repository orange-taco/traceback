from django.test import TestCase

from apps.accounts.serializers import KakaoOAuthSerializer


class KakaoOAuthSerializerTests(TestCase):
    def test_code_is_required_and_trimmed(self) -> None:
        serializer = KakaoOAuthSerializer(data={"code": " auth-code "})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data, {"code": "auth-code"})

    def test_rejects_missing_blank_and_too_long_code(self) -> None:
        missing = KakaoOAuthSerializer(data={})
        blank = KakaoOAuthSerializer(data={"code": " "})
        too_long = KakaoOAuthSerializer(data={"code": "x" * 1025})

        self.assertFalse(missing.is_valid())
        self.assertIn("code", missing.errors)
        self.assertFalse(blank.is_valid())
        self.assertIn("code", blank.errors)
        self.assertFalse(too_long.is_valid())
        self.assertIn("code", too_long.errors)
