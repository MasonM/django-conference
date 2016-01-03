from datetime import datetime, date
from freezegun import freeze_time

from django.test import TestCase

from django_conference.models import *


class MeetingTestCase(TestCase):
    @freeze_time("2012-01-14")
    def test_is_registration_active(self):
        old_meeting = Meeting(
            reg_start=date(2000, 1, 1),
            reg_deadline=date(2000, 2, 1)
        )
        self.assertFalse(old_meeting.registration_active())
