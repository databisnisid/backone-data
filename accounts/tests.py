import time
from datetime import timedelta

from axes.models import AccessAttempt
from django.conf import settings
from django.test import TestCase, override_settings

from .models import User


class AxesLockoutTest(TestCase):
    """Lockout MUST expire on its own, MUST NOT be extended by retries.

    Cites V52. The 2026-09-17 production lockout was caused by the django-axes
    default AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT=True: every attempt made
    while locked (even one with the correct password) rewrote attempt_time and
    restarted the full cool-off, so retrying never healed and the lockout looked
    permanent. AXES_COOLOFF_TIME was also a bare number, which django-axes reads
    as HOURS.
    """

    username = "locked@x.id"
    password = "rightpass"

    def setUp(self):
        User.objects.create_user(username=self.username, password=self.password)

    def _login(self, password):
        return self.client.post(
            "/api/auth/token/",
            {"username": self.username, "password": password},
            content_type="application/json",
        )

    def _attempt(self):
        return AccessAttempt.objects.filter(username=self.username).first()

    def test_cool_off_unit_is_explicit(self):
        """A bare int/float means HOURS to django-axes; the unit must be explicit."""
        self.assertIsInstance(settings.AXES_COOLOFF_TIME, timedelta)

    def test_retry_while_locked_does_not_extend_lockout(self):
        for _ in range(settings.AXES_FAILURE_LIMIT):
            self.assertEqual(self._login("WRONG").status_code, 401)
        locked = self._attempt()
        self.assertGreaterEqual(locked.failures_since_start, settings.AXES_FAILURE_LIMIT)

        # A retry — wrong password, then the CORRECT one — must not move the clock.
        self._login("WRONG")
        self._login(self.password)

        after = self._attempt()
        self.assertEqual(after.attempt_time, locked.attempt_time)
        self.assertEqual(after.failures_since_start, locked.failures_since_start)

    @override_settings(AXES_COOLOFF_TIME=timedelta(seconds=1))
    def test_lockout_expires_without_operator_intervention(self):
        for _ in range(settings.AXES_FAILURE_LIMIT):
            self._login("WRONG")
        self.assertEqual(self._login(self.password).status_code, 401)  # still locked

        time.sleep(1.2)  # window passes with no further attempts

        self.assertEqual(self._login(self.password).status_code, 200)
