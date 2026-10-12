from django.urls import reverse
from rest_framework.test import APITestCase


class HealthTests(APITestCase):
    def test_public_health_contract(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "swipe-iq-api"})
        self.assertEqual(response["Content-Type"], "application/json")

    def test_health_rejects_writes(self):
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse("health"), {}, format="json")
                self.assertEqual(response.status_code, 405)
