from django.test import SimpleTestCase


class HealthCheckTests(SimpleTestCase):
    def test_health_returns_ok_without_authentication(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_api_v1_namespace_exists(self) -> None:
        response = self.client.get("/api/v1/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})
