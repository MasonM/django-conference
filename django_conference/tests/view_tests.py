from datetime import date, datetime
import re
from freezegun import freeze_time

from django.core import mail
from django.test import TestCase

from django_conference.models import *


@freeze_time("2010-10-10 00:00:00")
class BaseTestCase(TestCase):
    "Base class for view tests"
    urls = 'django_conference.tests.urls'

    def create_user(self):
        return user_model.objects.create_user(username="foo@bar.com",
            email="foo@bar.com", password="foo")

    def login(self):
        user = self.create_user()
        self.client.login(username=user.username, password='foo')

    def create_active_meeting(
        self,
        location="SOMEWHERE",
        start=datetime(2010, 9, 9),
        end=datetime(2011, 9, 9)
    ):
        return Meeting.objects.create(
            is_active=True,
            location=location,
            start_date=start.date(),
            end_date=end.date(),
            reg_start=start.date(),
            reg_deadline=end.date(),
            early_reg_deadline=start.date(),
            paper_submission_start=start,
            paper_submission_end=end,
            session_submission_start=start,
            session_submission_end=end
        )


class HomepageTestCase(BaseTestCase):
    "Tests homepage() view"
    def __do_get(self):
        return self.client.get('/conference/')

    def test_with_no_meetings(self):
        self.assertContains(self.__do_get(), "No meetings found")

    def test_with_inactive_meeting(self):
        meeting = self.create_active_meeting()
        meeting.is_active = False
        meeting.save()
        self.assertContains(self.__do_get(), "No meetings found")

    def test_with_multiple_meetings(self):
        old_meeting = self.create_active_meeting(location="OLD",
            start=datetime(2000, 1, 1),
            end=datetime(2000, 2, 1))
        new_meeting = self.create_active_meeting(location="NEW",
            start=datetime(2010, 1, 1),
            end=datetime(2010, 11, 11))
        self.assertContains(self.__do_get(), "NEW 2010 Meeting Homepage")

    def test_registration_link(self):
        meeting = self.create_active_meeting()
        self.assertContains(self.__do_get(), "Register for the Meeting</a>")

        meeting.reg_deadline = date(2010, 10, 9)
        meeting.save()
        response = self.__do_get()
        self.assertContains(response, "The deadline for registration is over")

        meeting.reg_start = date(2010, 11, 11)
        meeting.reg_deadline = date(2010, 12, 12)
        meeting.save()
        response = self.__do_get()
        self.assertContains(response, "Registration will open Nov. 11, 2010")

    def test_submit_paper_link(self):
        meeting = self.create_active_meeting()
        self.assertContains(self.__do_get(), "Submit Paper or Poster</a>")

        meeting.paper_submission_end = datetime(2010, 10, 9)
        meeting.save()
        self.assertContains(self.__do_get(), "The deadline for paper/poster "+\
            "submission is over")

        meeting.paper_submission_start = datetime(2010, 11, 11)
        meeting.paper_submission_end = datetime(2010, 12, 12)
        meeting.save()
        # normalize white-space
        content = re.sub('\s+', ' ', self.__do_get().content)
        self.assertIn("Paper submissions will be accepted starting "+
            "Nov. 11, 2010", content)

    def test_submit_session_link(self):
        meeting = self.create_active_meeting()
        self.assertContains(self.__do_get(), "Submit Session</a>")

        meeting.session_submission_end = datetime(2010, 10, 9)
        meeting.save()
        self.assertContains(self.__do_get(), "The deadline for session "+\
            "submission is over")

        meeting.session_submission_start = datetime(2010, 11, 11)
        meeting.session_submission_end = datetime(2010, 12, 12)
        meeting.save()
        # normalize white-space
        content = re.sub('[\s\n]+', ' ', self.__do_get().content)
        self.assertIn("Session submissions will be accepted starting "+
            "Nov. 11, 2010", content)


class SubmitPaperTestCase(BaseTestCase):
    "Tests submit_paper() view"
    def __do_post(self, **kwargs):
        return self.client.post('/conference/submit_paper', kwargs,
            follow=True)

    def test_not_logged_in(self):
        response = self.client.get('/conference/submit_paper')
        self.assertRedirects(response,
            '/accounts/login/?next=/conference/submit_paper')

    def test_with_no_active_meeting(self):
        self.login()
        response = self.client.get('/conference/submit_paper')
        self.assertRedirects(response, '/conference/')

        meeting = self.create_active_meeting()
        meeting.paper_submission_start = datetime(3000, 1, 1)
        meeting.paper_submission_end = datetime(4000, 1, 1)
        meeting.save()
        response = self.client.get('/conference/submit_paper')
        self.assertRedirects(response, '/conference/')

    def test_missing_field_error_handling(self):
        self.login()
        self.create_active_meeting()
        data = {'first_name': 'f'}
        self.assertContains(self.__do_post(**data), 'This field is required')

        data['last_name'] = 'b'
        data['email'] = 'f@b.com'
        self.assertContains(self.__do_post(**data), 'This field is required')

        data['title'] = 'hi'
        self.assertContains(self.__do_post(**data), 'This field is required')

    def test_invalid_email_error_handling(self):
        self.login()
        self.create_active_meeting()
        response = self.__do_post(email="foo")
        self.assertContains(response, 'Enter a valid e-mail address.')

    def test_invalid_email_error_handling(self):
        self.login()
        self.create_active_meeting()
        response = self.__do_post(abstract="hi " * 100)
        self.assertContains(response, "Abstract can contain a maximum " +
            "of 10 words.")

    def test_submit_minimal_valid_paper(self):
        self.login()
        self.create_active_meeting()
        response = self.__do_post(
            first_name="foo",
            last_name="bar",
            email="foo@bar.com",
            title="TITLE",
            abstract="ABSTRACT",
            prior_sundays="0",
        )
        self.assertEqual(Paper.objects.count(), 1)
        paper_id = Paper.objects.all()[0].id
        self.assertRedirects(response, 
            '/conference/submit_success/%d/' % paper_id)
        msg = 'Your reference number is %d' % paper_id
        self.assertContains(response, msg)

        self.assertEqual(mail.outbox[0].subject, "Paper Submission Confirmation")
        self.assertEqual(mail.outbox[0].to, ['foo@bar.com'])
        self.assertIn(msg, mail.outbox[0].body)

    def test_submit_complete_valid_paper(self):
        self.login()
        self.create_active_meeting()
        response = self.__do_post(
            first_name="foo bar baz",
            last_name="bam foo bar",
            email="foo@bar.co.uk",
            title="SOME TITLE",
            abstract="ABSTRACT HELLO",
            coauthor="foo2 bar2",
            av_info="L",
            notes="NOTES",
            prior_sundays="1",
        )
        self.assertEqual(Paper.objects.count(), 1)
        paper_id = Paper.objects.all()[0].id
        self.assertRedirects(response, 
            '/conference/submit_success/%d/' % paper_id)
        self.assertContains(response, 'Your reference number is %d' % paper_id)
