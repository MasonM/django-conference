from datetime import date, datetime
import re
import decimal
from freezegun import freeze_time

from django.core import mail
from django.conf import settings
from django.test import TestCase

from django_conference import settings as conf_settings
from django_conference.models import *


@freeze_time("2010-10-10 00:00:00")
class BaseTestCase(TestCase):
    "Base class for view tests"
    urls = 'django_conference.tests.urls'

    def setUp(self):
        self.old_LOGIN_URL = getattr(settings, 'LOGIN_URL', None)
        settings.LOGIN_URL = '/account/'

        self.old_DJANGO_CONFERENCE_ABSTRACT_MAX_WORDS = \
            conf_settings.DJANGO_CONFERENCE_ABSTRACT_MAX_WORDS
        conf_settings.DJANGO_CONFERENCE_ABSTRACT_MAX_WORDS = 10

        self.old_DJANGO_CONFERENCE_DISABLE_PAYMENT_PROCESSING = \
            conf_settings.DJANGO_CONFERENCE_DISABLE_PAYMENT_PROCESSING
        conf_settings.DJANGO_CONFERENCE_DISABLE_PAYMENT_PROCESSING = True

    def tearDown(self):
        settings.LOGIN_URL = self.old_LOGIN_URL
        conf_settings.DJANGO_CONFERENCE_ABSTRACT_MAX_WORDS = \
            self.old_DJANGO_CONFERENCE_ABSTRACT_MAX_WORDS
        conf_settings.DJANGO_CONFERENCE_DISABLE_PAYMENT_PROCESSING = \
            self.old_DJANGO_CONFERENCE_DISABLE_PAYMENT_PROCESSING

    def create_user(self, username='foo@bar.com'):
        return user_model.objects.create_user(username=username,
            email=username, password="foo")

    def login(self, user):
        self.client.login(username=user.username, password='foo')

    def create_active_meeting(self,
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
    post_data_for_valid_paper = {
        'first_name': 'foo',
        'last_name': 'bar',
        'email': 'foo@bar.com',
        'title': 'TITLE',
        'abstract': 'ABSTRACT',
        'prior_sundays': '0',
    }

    def __do_post(self, **kwargs):
        return self.client.post('/conference/submit_paper', kwargs,
            follow=True)

    def test_not_logged_in(self):
        response = self.client.get('/conference/submit_paper')
        self.assertRedirects(response,
            '/account/?next=/conference/submit_paper')

    def test_with_no_active_meeting(self):
        self.login(self.create_user())
        response = self.client.get('/conference/submit_paper')
        self.assertRedirects(response, '/conference/')

        meeting = self.create_active_meeting()
        meeting.paper_submission_start = datetime(3000, 1, 1)
        meeting.paper_submission_end = datetime(4000, 1, 1)
        meeting.save()
        response = self.client.get('/conference/submit_paper')
        self.assertRedirects(response, '/conference/')

    def test_invalid_email_error_handling(self):
        self.login(self.create_user())
        self.create_active_meeting()
        response = self.__do_post(email="foo")
        self.assertContains(response, 'Enter a valid e-mail address.')

    def test_abstract_too_long_error_handling(self):
        self.login(self.create_user())
        self.create_active_meeting()
        response = self.__do_post(abstract="hi " * 100)
        self.assertContains(response, "Abstract can contain a maximum " +
            "of 10 words.")

    def test_missing_field_error_handling(self):
        self.login(self.create_user())
        self.create_active_meeting()
        for field in self.post_data_for_valid_paper.keys():
            data = self.post_data_for_valid_paper.copy()
            del data[field]
            self.assertContains(self.__do_post(**data), 'This field is required')

    def test_submit_minimal_valid_paper(self):
        self.login(self.create_user())
        self.create_active_meeting()
        response = self.__do_post(**self.post_data_for_valid_paper)
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
        user = self.create_user()
        self.login(user)
        self.create_active_meeting()
        post_data = self.post_data_for_valid_paper.copy()
        post_data.update({
            'coauthor': "foo2 bar2",
            'av_info': "L",
            'notes': "NOTES",
        })
        response = self.__do_post(**post_data)
        self.assertEqual(Paper.objects.count(), 1)
        paper = Paper.objects.all()[0]
        self.assertRedirects(response, 
            '/conference/submit_success/%d/' % paper.id)
        self.assertContains(response, 'Your reference number is %d' % paper.id)
        self.assertEqual(paper.submitter, user)
        self.assertEqual(paper.presenter.first_name, post_data['first_name'])
        self.assertEqual(paper.presenter.last_name, post_data['last_name'])
        self.assertEqual(paper.presenter.email, post_data['email'])
        self.assertEqual(paper.title, post_data['title'])
        self.assertEqual(paper.abstract, post_data['abstract'])
        self.assertEqual(paper.coauthor, post_data['coauthor'])
        self.assertEqual(paper.av_info, post_data['av_info'])
        self.assertEqual(paper.notes, post_data['notes'])
        self.assertEqual(paper.prior_sundays, post_data['prior_sundays'])


class EditPaperTestCase(BaseTestCase):
    "Tests edit_paper() view"
    def setUp(self):
        super(EditPaperTestCase, self).setUp()
        self.paper = Paper.objects.create(
            submitter=self.create_user(),
            presenter=PaperPresenter.objects.create(
                first_name="FOO",
                last_name="BAR",
                email="foo@bar.com",
            ),
            title="HELLO",
            abstract="HI",
        )

    def __do_get(self, paper_id, **kwargs):
        return self.__do_method(self.client.get, paper_id, kwargs)

    def __do_post(self, paper_id, **kwargs):
        return self.__do_method(self.client.post, paper_id, kwargs)

    def __do_method(self, method, paper_id, args):
        return method('/conference/edit_paper/%d' % paper_id, args,
            follow=True)

    def test_not_logged_in(self):
        response = self.__do_get(self.paper.id)
        self.assertRedirects(response,
            '/account/?next=/conference/edit_paper/%d' % self.paper.id)

    def test_wrong_user(self):
        user = self.create_user("SOMEONE ELSE")
        self.login(user)
        response = self.__do_get(self.paper.id)
        self.assertContains(response, 'According to our records, you are '+
            'not the submitter')

    def test_with_invalid_paper(self):
        self.login(self.paper.submitter)
        response = self.__do_get(9999)
        self.assertRedirects(response, '/conference/')

    def test_submit_valid_edits(self):
        self.login(self.paper.submitter)
        response = self.__do_get(self.paper.id)
        self.assertContains(response, 'Edit Paper')

        data = SubmitPaperTestCase.post_data_for_valid_paper
        data.update({
            'title': "CHANGED TITLE",
            'abstract': "CHANGED ABSTRACT",
        })
        response = self.__do_post(self.paper.id, **data)
        self.assertContains(response, 'Your paper has been updated')

        paper = Paper.objects.get(id=self.paper.id)
        self.assertEqual(paper.title, 'CHANGED TITLE')
        self.assertEqual(paper.abstract, 'CHANGED ABSTRACT')


class SubmitSessionTestCase(BaseTestCase):
    "Tests submit_session() and submit_session_papers() views"
    post_data_for_valid_session = {
        'title': 'session title',
        'num_papers': 4,
        'first_name': 'b',
        'last_name': 'b',
        'type': 'O',
        'email': 'f@b.com',
        'institution': 'UFL',
        'chair-first_name': 'c',
        'chair-last_name': 'c',
        'chair-gender': 'O',
        'chair-type': 'O',
        'chair-email': 'g@c.com',
        'chair-institution': 'UW',
    }
    post_data_for_valid_commentator = {
        'commentator-first_name': 'd',
        'commentator-last_name': 'd',
        'commentator-email': 'h@d.com',
        'commentator-institution': 'UM',
    }

    def __do_post(self, **kwargs):
        return self.client.post('/conference/submit_session', kwargs,
            follow=True)

    def test_not_logged_in(self):
        response = self.client.get('/conference/submit_session')
        self.assertRedirects(response,
            '/account/?next=/conference/submit_session')

    def test_with_no_active_meeting(self):
        self.login(self.create_user())
        response = self.client.get('/conference/submit_session')
        self.assertRedirects(response, '/conference/')

        meeting = self.create_active_meeting()
        meeting.session_submission_start = datetime(3000, 1, 1)
        meeting.session_submission_end = datetime(4000, 1, 1)
        meeting.save()
        response = self.client.get('/conference/submit_session')
        self.assertRedirects(response, '/conference/')

    def test_missing_field_error_handling(self):
        self.login(self.create_user())
        self.create_active_meeting()
        for field in self.post_data_for_valid_session.keys():
            data = self.post_data_for_valid_session.copy()
            del data[field]
            self.assertContains(self.__do_post(**data), 'This field is required')

    def test_needs_commentator_error_handling(self):
        self.login(self.create_user())
        self.create_active_meeting()

        post_data = self.post_data_for_valid_session.copy()
        post_data['num_papers'] = 3
        self.assertContains(self.__do_post(**post_data),
            'must have a commentator')

        for field in self.post_data_for_valid_commentator.keys():
            post_data.update(self.post_data_for_valid_commentator)
            del post_data[field]
            self.assertContains(self.__do_post(**post_data),
                'Please fill in all the')

    def test_invalid_email_error_handling(self):
        self.login(self.create_user())
        self.create_active_meeting()
        response = self.__do_post(email="foo")
        self.assertContains(response, 'Enter a valid e-mail address.')

    def test_abstract_too_long_error_handling(self):
        self.login(self.create_user())
        self.create_active_meeting()
        response = self.__do_post(abstract="hi " * 100)
        self.assertContains(response, "Abstract can contain a maximum " +
            "of 10 words.")

    def assertSessionMatchesPostData(self, session, post_data):
        self.assertEqual(session.title, post_data['title'])
        self.assertEqual(session.papers.count(), post_data['num_papers'])
        for cadre, post_prefix in {
            session.organizers: '',
            session.chairs: 'chair-',
            session.commentators: 'commentator-',
        }.iteritems():
            self.assertEqual(cadre.count(), 1)
            for field in ['first_name', 'last_name', 'email', 'institution']:
                self.assertEqual(getattr(cadre.all()[0], field),
                    post_data[post_prefix + field])

    def test_submit_complete_session(self):
        user = self.create_user()
        self.login(user)
        meeting = self.create_active_meeting()
        session_post_data = self.post_data_for_valid_session.copy()
        session_post_data.update(self.post_data_for_valid_commentator)
        response = self.__do_post(**session_post_data)
        self.assertRedirects(response, '/conference/submit_session_papers')

        # Should wait until the papers have been submitted before creation
        self.assertEqual(Session.objects.count(), 0)

        paper_post_data = SubmitPaperTestCase.post_data_for_valid_paper
        post_data = paper_post_data.copy()
        for paper_num in range(1, 4):
            post_data.update(dict([
                ('%d-%s' % (paper_num, field), value)
                for field, value in paper_post_data.iteritems()
            ]))
        response = self.client.post('/conference/submit_session_papers',
            post_data, follow=True)
        self.assertEqual(Session.objects.count(), 1)
        session = Session.objects.all()[0]
        self.assertEqual(session.meeting, meeting)
        self.assertEqual(session.submitter, user)
        self.assertFalse(session.accepted)
        self.assertSessionMatchesPostData(session, session_post_data)

        self.assertRedirects(response, 
            '/conference/submit_success/%d/' % session.id)
        msg = 'Your reference number is %d' % session.id
        self.assertContains(response, msg)

        self.assertEqual(mail.outbox[0].subject, "Session Submission Confirmation")
        self.assertEqual(mail.outbox[0].to, ['f@b.com'])
        self.assertIn(msg, mail.outbox[0].body)


class RegisterTestCase(BaseTestCase):
    "Tests register() and payment() views"
    def setUp(self):
        super(RegisterTestCase, self).setUp()
        self.online_reg = self.create_user("OnlineRegistration")
        self.meeting = self.create_active_meeting()
        self.paid_option = self.meeting.regoptions.create(
            option_name="TEST OPTION 1",
            early_price=10.10,
            regular_price=20.20,
            onsite_price=20.20,
        )
        self.free_option = self.meeting.regoptions.create(
            option_name="TEST OPTION 2",
            early_price=0,
            regular_price=0,
            onsite_price=0,
        )
        self.donation1 = self.meeting.donations.create(
            donate_type=DonationType.objects.create(name="DONATE1", label="!"),
        )
        self.extra1 = self.meeting.extras.create(
            extra_type=ExtraType.objects.create(name="EXTRA1", label="!"),
            price=10,
            max_quantity=10,
        )

    def assertRegistrationEmailSent(self, user):
        self.assertEqual(mail.outbox[0].subject, "2010 Meeting Registration")
        self.assertEqual(mail.outbox[0].to, [user.email])
        self.assertIn('You have been successfully registered',
            mail.outbox[0].body)

    def __do_post(self, **kwargs):
        kwargs['registerMeeting'] = 'Submit'
        return self.client.post('/conference/register', kwargs,
            follow=True)

    def test_not_logged_in(self):
        response = self.client.get('/conference/register')
        self.assertRedirects(response,
            '/account/?next=/conference/register')

    def test_missing_field_error_handling(self):
        self.login(self.create_user())
        self.assertContains(self.__do_post(), 'This field is required')

    def test_register_with_free_option(self):
        user = self.create_user()
        self.login(user)
        response = self.__do_post(
            type=self.free_option.id,
            guest_first_name="FOO",
            guest_last_name="BAR",
            special_needs="MORE TESTS",
        )
        self.assertRedirects(response, '/conference/register_success')

        self.assertRegistrationEmailSent(user)

        self.assertEqual(Registration.objects.count(), 1)
        registration = Registration.objects.all()[0]
        self.assertEqual(registration.meeting, self.meeting)
        self.assertEqual(registration.registrant, user)
        self.assertEqual(registration.type, self.free_option)
        self.assertEqual(registration.special_needs, 'MORE TESTS')
        self.assertEqual(registration.guests.count(), 1)
        guest = registration.guests.all()[0]
        self.assertEqual(guest.first_name, 'FOO')
        self.assertEqual(guest.last_name, 'BAR')

    def test_register_with_paid_option(self):
        user = self.create_user()
        self.login(user)
        response = self.__do_post(type=self.paid_option.id)
        self.assertRedirects(response, '/conference/payment/')
        self.assertRegexpMatches(response.content, 'class="orderTotal">\s*\$20.20')

        # Payment authorization is disabled in tests
        response = self.client.post('/conference/payment/', {
            'stripeToken': 'dummy',
        })
        self.assertRedirects(response, '/conference/register_success')

        self.assertRegistrationEmailSent(user)

        self.assertEqual(Registration.objects.count(), 1)
        registration = Registration.objects.all()[0]
        self.assertEqual(registration.meeting, self.meeting)
        self.assertEqual(registration.registrant, user)
        self.assertEqual(registration.type, self.paid_option)
        self.assertEqual(registration.guests.count(), 0)

    def test_register_with_extra_and_donation(self):
        user = self.create_user()
        self.login(user)
        response = self.__do_post(
            type=self.free_option.id,
            EXTRA1='5',
            DONATE1='123.45',
        )
        self.assertRedirects(response, '/conference/payment/')
        self.assertRegexpMatches(response.content,
            'class="orderTotal">\s*\$173.45')

        response = self.client.post('/conference/payment/', {
            'stripeToken': 'dummy',
        })
        self.assertRedirects(response, '/conference/register_success')

        self.assertRegistrationEmailSent(user)

        self.assertEqual(Registration.objects.count(), 1)
        registration = Registration.objects.all()[0]

        self.assertEqual(registration.regextras.count(), 1)
        regextra = registration.regextras.all()[0]
        self.assertEqual(regextra.extra, self.extra1)
        self.assertEqual(regextra.quantity, 5)

        self.assertEqual(registration.regdonations.count(), 1)
        regdonation = registration.regdonations.all()[0]
        self.assertEqual(regdonation.donate_type, self.donation1)
        self.assertEqual(regdonation.total, Decimal('123.45'))

    def test_pay_for_nonexistent_registration(self):
        self.login(self.create_user())
        response = self.client.get('/conference/payment/39999')
        self.assertEqual(response.status_code, 404)

    def test_pay_for_existing_registration(self):
        user = self.create_user()
        self.login(user)
        registration = Registration(
            meeting=self.meeting,
            registrant=user,
            type=self.paid_option,
            entered_by=self.online_reg,
        )
        registration.save()
        url = '/conference/payment/%d' % registration.id

        response = self.client.get(url)
        self.assertContains(response, 'Please pay for the following')
        self.assertRegexpMatches(response.content, 'class="orderTotal">\s*\$20.20')

        response = self.client.post(url, {'stripeToken': 'dummy'}, follow=True)
        self.assertRedirects(response, '/conference/paysuccess')
        self.assertContains(response, 'Thank you for paying')
