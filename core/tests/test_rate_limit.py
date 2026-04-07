from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.cache import caches
from rest_framework import status 


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class RateLimitTests(TestCase):
    def setUp(self):
        self.client.defaults["wsgi.url_scheme"] = "http"
        self.cache = caches["default"]
        self.cache.clear()

    def test_anon_rate_limit_exceeded(self):
        # Use a simple endpoint: index page
        url = reverse("index")
        # default anon limit is 60/min; we'll temporarily set it low
        with self.settings(RATE_LIMIT_ANON="2/min"):
            # first two should pass
            r1 = self.client.get(url)
            self.assertEqual(r1.status_code, status.HTTP_200_OK)
            r2 = self.client.get(url)
            self.assertEqual(r2.status_code, status.HTTP_200_OK)
            # third should be 429
            r3 = self.client.get(url)
            self.assertEqual(r3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_user_rate_limit_exceeded(self):
        url = reverse("index")
        # Create a user and login
        from django.contrib.auth.models import User

        User.objects.create_user("rluser", password="pass")
        self.client.login(username="rluser", password="pass")
        with self.settings(RATE_LIMIT_USER="2/min"):
            r1 = self.client.get(url)
            self.assertEqual(r1.status_code, status.HTTP_200_OK)
            r2 = self.client.get(url)
            self.assertEqual(r2.status_code, status.HTTP_200_OK)
            r3 = self.client.get(url)
            self.assertEqual(r3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
