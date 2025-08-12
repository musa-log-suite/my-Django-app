from rest_framework.test import APIClient
from django.test import TestCase
import sys

class WalletAccessTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_debug_terminal_echo(self):
        sys.stdout.write("🛠 Running debug test: checking stdout\n")
        sys.stderr.write("🧨 Running debug test: checking stderr\n")
        
        # Toggle this to False when done confirming test execution
        DEBUG_FAIL = True
        if DEBUG_FAIL:
            assert False, "💥 Intentional failure to prove test is running"

    def test_unauthorized_access_to_wallet_me(self):
        sys.stdout.write("🔐 Checking unauthorized access to /api/wallet/me/\n")
        response = self.client.get("/api/wallet/me/")

        expected_codes = [401, 403]
        msg = f"Expected response status in {expected_codes}, got {response.status_code}"
        self.assertIn(response.status_code, expected_codes, msg)

        detail = str(response.data.get("detail", "")).lower()
        self.assertTrue(
            "authentication" in detail or "credentials" in detail,
            f"Expected auth-related error message, got: {detail}"
        )