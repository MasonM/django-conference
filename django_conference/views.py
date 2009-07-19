import pickle
from decimal import Decimal

from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect

from django_conference import settings
from django_conference.forms import (PaperForm, MeetingSessions,
    MeetingRegister, MeetingExtras, MeetingDonations, SessionForm,
    SessionCadreForm, PaymentForm)
from django_conference.models import Meeting, Registration, Paper


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
    meeting = Meeting.objects.latest()
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
    })


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
        meeting = Meeting.objects.latest()

    address_form_loc = settings.DJANGO_CONFERENCE_ADDRESS_FORM
    address_form = __import__(name=address_form_loc[0],
        form_list=[address_form_loc[1]])

    if 'payMeeting' in request.POST:
        payment_data = None
        address_form = address_form(request.POST)
        payment_form = PaymentForm(data=request.POST)
        if address_form.is_valid():
            payment_data = address_form.clean()
            payment_data.update({
                'total': cont.get_total(),
                'email': request.user.email,
                'description': cont.get_description(),
            })
            payment_form.payment_data = payment_data
            if payment_form.is_valid():
                #save registration and send an e-mail
                if address_form and address_form.is_valid():
                    address_form.save(request.user, "B")
                if reg_id:
                    url = reverse("django_conference_paysuccess")
                else:
                    cont.save()
                    cont.registration.send_register_email()
                    del request.session['regContainer']
                    url = reverse("django_conference_register_success")
                return HttpResponseRedirect(url)
    else:
        initial_data = request.POST or {}
        payment_form = PaymentForm(initial=initial_data)
        address_form = address_form(initial=initial_data)

    return render_to_response('django_conference/payment.html', {
        'payment_form': payment_form,
        'address_form': address_form,
        'meeting': meeting,
        'regCont': cont,
        'notice': notice,
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
    })


@login_required
def submit_session(request):
    """
    Allows users to submit a session for approval
    """
    meeting = Meeting.objects.latest()
    if not meeting.can_submit_session():
        return HttpResponseRedirect(reverse("django_conference_home"))

    session_form = SessionForm(request.POST or None)
    organizer_form = SessionCadreForm(request.POST or None, optional=False)
    chair_form = SessionCadreForm(request.POST or None, prefix="chair")
    commentator_form = SessionCadreForm(request.POST or None,
        prefix="commentator")

    if request.POST and all(f.is_valid() for f in [session_form,
        organizer_form, chair_form, commentator_form]):

        session = session_form.save(meeting=meeting)
        organizer = organizer_form.save()
        session.organizers.add(organizer)
        if chair_form.has_entered_info():
            chair = chair_form.save()
            session.chair = chair
        if commentator_form.has_entered_info():
            commentator = commentator_form.save()
            session.commentators.add(commentator)
        session.save()
        session.send_submission_email()
        kwargs = {'id': session.id}
        url = reverse('django_conference_submission_success', kwargs=kwargs)
        return HttpResponseRedirect(url)

    return render_to_response('django_conference/submit_session.html', {
        'session_form': session_form,
        'organizer_form': organizer_form,
        'chair_form': chair_form,
        'commentator_form': commentator_form,
        'meeting': meeting,
        'contact_email': settings.DJANGO_CONFERENCE_CONTACT_EMAIL,
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
    })


def submission_success(request, id=None):
    message = 'Your reference number is %s.' % id
    return render_to_response('django_conference/submission_success.html', {
        'message': message,
        'meeting': Meeting.objects.latest(),
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
    })


@login_required
def submit_paper(request):
    """
    Allow users to submit a paper for approval
    """
    meeting = Meeting.objects.latest()
    if not meeting.can_submit_paper():
        return HttpResponseRedirect(reverse("django_conference_home"))
    paper_form = PaperForm(request.POST or None)

    if request.POST and paper_form.is_valid():
        paper = paper_form.save(request.user)
        paper.send_submission_email()
        kwargs = {'id': paper.id}
        url = reverse('django_conference_submission_success', kwargs=kwargs)
        return HttpResponseRedirect(url)
    return render_to_response('django_conference/submit_paper.html', {
        'paper_form': paper_form,
        'meeting': meeting,
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
    })


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
    if paper.presenter != request.user:
        email = settings.DJANGO_CONFERENCE_CONTACT_EMAIL
        notice = 'According to our records, you are not the presenter for '+\
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
    })


def homepage(request):
    return render_to_response('django_conference/homepage.html', {
        'meeting': Meeting.objects.latest(),
        'media_root': settings.DJANGO_CONFERENCE_MEDIA_ROOT,
    })
