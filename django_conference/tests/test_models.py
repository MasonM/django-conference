from datetime import datetime, date
from freezegun import freeze_time

from django.test import TestCase

from django_conference.models import *


class MeetingTestCase(TestCase):
    "Test for Meeting model"
    def __do_test_daterange_method(self, start_field, end_field, method,
        date_or_datetime):
        """
        Generic tester for a method that checks if the current date is between
        two fields, start_field and end_field.
        """
        meeting = Meeting()
        date_ranges_to_check = {
            ((2012, 10, 9), (2012, 10, 9)): False,
            ((2012, 10, 9), (2012, 10, 10)): True,
            ((2012, 10, 10), (2012, 11, 11)): True,
            ((2012, 10, 15), (2012, 11, 11)): False,
        }
        freeze_time("2012-10-10 00:00:00").start()
        for date_range, expected_result in date_ranges_to_check.iteritems():
            setattr(meeting, start_field, date_or_datetime(*date_range[0]))
            setattr(meeting, end_field, date_or_datetime(*date_range[1]))
            msg = "Failed asserting Meeting.%s() returns %s with %s=%d-%d-%d"+\
                " and %s=%d-%d-%d"
            msg_args = (method, expected_result, start_field) + \
                date_range[0] + (end_field,) + date_range[1]
            self.assertEquals(expected_result, getattr(meeting, method)(),
                msg=msg % msg_args)

    def test_is_registration_active(self):
        self.__do_test_daterange_method('reg_start', 'reg_deadline',
            'registration_active', date)

    def test_can_submit_paper(self):
        self.__do_test_daterange_method('paper_submission_start',
            'paper_submission_end', 'can_submit_paper', datetime)

    def test_can_submit_session(self):
        self.__do_test_daterange_method('session_submission_start',
            'session_submission_end', 'can_submit_session', datetime)
