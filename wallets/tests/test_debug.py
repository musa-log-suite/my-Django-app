from django.test import TestCase

class DebugTestCase(TestCase):
    def test_sanity_check(self):
        print("✅ Debug test ran!")
        assert 1 + 1 == 2
