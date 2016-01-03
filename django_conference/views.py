import pickle
from decimal import Decimal
from datetime import datetime, date

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect

from django_conference import settings
from django_conference.forms import (PaperForm, MeetingSessions,
    MeetingRegister, MeetingExtras, MeetingDonations, SessionForm,
    SessionCadreForm, PaymentForm, PaperPresenterForm)
from django_conference.models import (Meeting, Registration, Paper,
    SessionPapers)


class RegistrationContainer(object):
    """
    Container to contain unsaved Registration, Session, RegistrationExtra,
    and RegistrationDonation objects until they can be saved.
    """
    def __init__(self, registration, guest, extras, donations,
        sessions, page1_cache):
        self.registration = registration
        self.guest = guest
        self.extras = extras
        self.donations = donations
        self.sessions = sessions
        # cache of POST data so fields can be filled in if registrant returns
        # to first page after getting to payment page
        self.page1_cache = page1_cache

    def save(self):
        """
        Saves Registration and sets sessions Many2Many relation if the
        registrant chose any sessions. Then, any donations or extras are
        associated with the registration and saved
        """
        self.registration.save()
        if self.sessions:
            self.registration.sessions = self.sessions
        if self.guest:
            self.guest.registration = self.registration
            self.guest.save()
        for x in self.extras + self.donations:
            x.registration = self.registration
            x.save()

    def get_total(self):
        """
        Implements Registration.get_total() for the unsaved Registration object
        """
        total = self.registration.get_meeting_cost()
        total += sum(e.get_total() for e in self.extras)
        total += sum(d.total for d in self.donations)
        return total

    def get_description(self):
        """ Get a string describing all the registration information."""
        desc = unicode(self.registration.type) + ", Meeting Registration"
        for extra in (self.extras + self.donations):
            desc += ", "+unicode(extra)
        return desc


@login_required
def register(request):
    meeting = Meeting.current_or_none()
    if not meeting or not meeting.can_register(request.user):
        #if user can't register, take them back
        return HttpResponseRedirect(settings.LOGIN_URL)

    if 'registerMeeting' in request.POST:
        register_form = MeetingRegister(meeting, data=request.POST)
        session_form = MeetingSessions(meeting, data=request.POST)
        extras_form = MeetingExtras(meeting, data=request.POST)
        donations_form = MeetingDonations(meeting, data=request.POST)
        forms = [register_form, extras_form, session_form, donations_form]
        if all(f.is_valid() for f in forms):
            extras = extras_form.get_extras(request.user)
            cont = RegistrationContainer(
                register_form.get_registration(request.user),
                register_form.get_guest(),
                extras,
                donations_form.get_donations(),
                session_form.get_sessions(),
                request.POST)
            if cont.get_total() == Decimal("0.00"):
                # they must have registered with a free option, so no
                # payment is necessary
                cont.registration.payment_type = "na"
                cont.save()
                cont.registration.send_register_email()
                if 'regContainer' in request.session:
                    del request.session['regContainer']
                url = reverse("django_conference_register_success")
            else:
                #don't save registration object yet since we haven't
                #received payment.
                request.session['regContainer'] = pickle.dumps(cont)
                url = reverse("django_conference_payment")
            return HttpResponseRedirect(url)
    else:
        cont = request.session.get('regContainer')
        previous_data = pickle.loads(cont).page1_cache if cont else None
        initial_data = request.POST or previous_data or {}
        register_form = MeetingRegister(meeting, initial=initial_data)
        session_form = MeetingSessions(meeting, initial=initial_data)
        extras_form = MeetingExtras(meeting, initial=initial_data)
        donations_form = MeetingDonations(meeting, initial=initial_data)

    return render_to_response('django_conference/register.html', {
        'register_form': register_form,
        'session_form': session_form,
        'extras_form': extras_form,
        'donations_form': donations_form,
        'meeting': meeting,
        'registrant': request.user,
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
    }, context_instance=RequestContext(request))


@login_required
def payment(request, reg_id=None):
    """
    Handles processing payment for a meeting registration.
    Allows both saved and unsaved registrations to be paid for. The former
    requires that the ID of the registration be passed as reg_id.
    """
    notice = ""
    if reg_id:
        registration = get_object_or_404(Registration, pk=reg_id)
        extras = list(registration.regextras.all())
        donations = list(registration.regdonations.all())
        sessions = list(registration.sessions.all())
        cont = RegistrationContainer(
            registration, None, extras, donations, sessions, None)
        meeting = registration.meeting
        notice = "Please pay for the following meeting registration."
    elif 'previous' in request.POST or 'regContainer' not in request.session:
        #either they shouldn't be here or they clicked "Previous" button
        return HttpResponseRedirect(reverse("django_conference_register"))
    else:
        cont = pickle.loads(request.session['regContainer'])
        meeting = Meeting.current()

    payment_error = ''
    if 'stripeToken' in request.POST:
        payment_form = PaymentForm({
            'total': cont.get_total(),
            'description': cont.get_description(),
            'stripeToken': request.POST['stripeToken'],
        })
        if payment_form.is_valid():
            #save registration and send an e-mail
            if reg_id:
                url = reverse("django_conference_paysuccess")
            else:
                cont.save()
                cont.registration.send_register_email()
                del request.session['regContainer']
                url = reverse("django_conference_register_success")
            return HttpResponseRedirect(url)
        else:
            payment_error = payment_form.last_error

    return render_to_response('django_conference/payment.html', {
        'payment_error': payment_error,
        'meeting': meeting,
        'regCont': cont,
        'notice': notice,
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
        'stripe_key': settings.DJANGO_CONFERENCE_STRIPE_PUBLISHABLE_KEY,
    }, context_instance=RequestContext(request))


@login_required
def submit_session(request):
    """
    Allows users to submit a session for approval
    """
    meeting = Meeting.current_or_none()
    if not meeting or not meeting.can_submit_session():
        return HttpResponseRedirect(reverse("django_conference_home"))

    session_form = SessionForm(request.POST or None)
    organizer_form = SessionCadreForm(request.POST or None, optional=False)
    organizer_form.fields['gender'].required = False
    chair_form = SessionCadreForm(request.POST or None, optional=False,
        prefix="chair")
    commentator_form = SessionCadreForm(request.POST or None,
        prefix="commentator")
    errors = {}

    if request.POST and all(f.is_valid() for f in [session_form,
        organizer_form, chair_form, commentator_form]):
        num_papers = session_form.cleaned_data['num_papers']
        if int(num_papers) == 3 and not commentator_form.has_entered_info():
            errors = {'Paper Abstracts': ['Sessions with 3 papers '+\
                'must have a commentator.']}
        else:
            request.session['session_data'] = pickle.dumps(request.POST)
            url = reverse('django_conference_submit_session_papers')
            return HttpResponseRedirect(url)

    return render_to_response('django_conference/submit_session.html', {
        'session_form': session_form,
        'organizer_form': organizer_form,
        'chair_form': chair_form,
        'commentator_form': commentator_form,
        'meeting': meeting,
        'contact_email': settings.DJANGO_CONFERENCE_CONTACT_EMAIL,
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
        'error_dict': errors.items(),
    }, context_instance=RequestContext(request))


@login_required
def submit_session_papers(request):
    meeting = Meeting.current()
    if not meeting.can_submit_session() or \
        'session_data' not in request.session:
        return HttpResponseRedirect(reverse("django_conference_home"))

    session_data = pickle.loads(request.session['session_data'])
    num = int(session_data['num_papers'])
    forms = []
    for i in range(num):
        forms.append(PaperPresenterForm(request.POST or None, prefix=i))
        forms.append(PaperForm(request.POST or None, prefix=i))

    if request.POST and all([x.is_valid() for x in forms]):
        session_form = SessionForm(session_data)
        session = session_form.save(meeting=meeting, submitter=request.user)

        organizer_form = SessionCadreForm(session_data)
        organizer = organizer_form.save()
        session.organizers.add(organizer)

        chair_form = SessionCadreForm(session_data, prefix="chair")
        chair = chair_form.save()
        session.chairs.add(chair)

        commentator_form = SessionCadreForm(session_data, prefix="commentator")
        commentator_form.is_valid()
        if commentator_form.has_entered_info():
            commentator = commentator_form.save()
            session.commentators.add(commentator)

        position = 1
        for i in range(0, num * 2, 2):
            paper_presenter = forms[i].save()
            paper = forms[i + 1].save(request.user, paper_presenter)
            SessionPapers.objects.create(session=session, paper=paper,
                position=position)
            position += 1

        session.save()
        session.send_submission_email()
        kwargs = {'id': session.id}
        url = reverse('django_conference_submission_success', kwargs=kwargs)
        return HttpResponseRedirect(url)

    return render_to_response('django_conference/submit_paper.html', {
        'forms': forms,
        'meeting': meeting,
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
    }, context_instance=RequestContext(request))


def submission_success(request, id=None):
    message = 'Your reference number is %s.' % id
    return render_to_response('django_conference/submission_success.html', {
        'message': message,
        'meeting': Meeting.current(),
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
    })


@login_required
def submit_paper(request):
    """
    Allow users to submit a paper for approval
    """
    meeting = Meeting.current_or_none()
    if not meeting or not meeting.can_submit_paper():
        return HttpResponseRedirect(reverse("django_conference_home"))

    paper_form = PaperForm(request.POST or None)
    paper_presenter_form = PaperPresenterForm(request.POST or None)

    if request.POST and paper_form.is_valid() and \
        paper_presenter_form.is_valid():
        presenter = paper_presenter_form.save()
        paper = paper_form.save(request.user, presenter)
        paper.send_submission_email()
        kwargs = {'id': paper.id}
        url = reverse('django_conference_submission_success', kwargs=kwargs)
        return HttpResponseRedirect(url)

    return render_to_response('django_conference/submit_paper.html', {
        'forms': [paper_presenter_form, paper_form],
        'meeting': meeting,
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
    }, context_instance=RequestContext(request))


@login_required
def edit_paper(request, paper_id):
    """
    Allow paper submitters to edit their paper. Only the user that submitted
    the paper is allowed to edit it.
    """
    try:
        paper = Paper.objects.get(id=paper_id)
    except Paper.DoesNotExist:
        return HttpResponseRedirect(reverse("django_conference_home"))
    notice = ""
    paper_form = None
    if paper.submitter != request.user:
        email = settings.DJANGO_CONFERENCE_CONTACT_EMAIL
        notice = 'According to our records, you are not the submitter for '+\
            'the paper "%s" and thus may not edit it. If you believe this '+\
            'to be an error, please contact <a href="mailto:%s">%s</a>.'
        notice = notice % (unicode(paper), email, email)
    else:
        paper_form = PaperForm(request.POST or None, instance=paper)
        if request.POST and paper_form.is_valid():
            paper_form.save(request.user)
            notice = "Your paper has been updated"

    return render_to_response('django_conference/edit_paper.html', {
        'paper_form': paper_form,
        'notice': notice,
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
    }, context_instance=RequestContext(request))


def homepage(request):
    meeting = Meeting.current_or_none()
    return render_to_response('django_conference/homepage.html', {
        'meeting': meeting,
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
        'reg_deadline_passed': meeting and date.today() > meeting.reg_deadline,
        'session_deadline_passed': meeting and \
            datetime.now() > meeting.session_submission_end,
        'paper_deadline_passed': meeting and \
            datetime.now() > meeting.paper_submission_end,
    })
