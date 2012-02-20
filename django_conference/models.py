from datetime import date, datetime, time
from decimal import Decimal
import re

from django.db import models
from django.db.models import Q
from django.db.models import get_model
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string

from django_conference import settings


user_model = get_model(*settings.DJANGO_CONFERENCE_USER_MODEL)


def meeting_stat(stat_func):
    """
    Decorator for a method that returns a list of dictionaries representing
    statistics for a given meeting, each dictionary containing 3 entries:
        1) A description
        2) A quantity
        3) A price
    The decorator appends a "Total" dict to the end if the returned list
    is non-empty.
    """
    def add_total(*args):
        stats = stat_func(*args)
        if stats:
            stats.append({
                "type": 'Total',
                "quantity": sum(o['quantity'] for o in stats),
                "income": sum(o['income'] for o in stats),
            })
        return stats
    return add_total


class Meeting(models.Model):
    """Model for conferences/meetings"""
    is_active = models.BooleanField(default=False,
        help_text="Check this to allow meeting registration and "+\
        "paper submission.")
    location = models.CharField(max_length=45,
        help_text='General location for where this meeting is taking '+\
                  'place, e.g. "Gainesville, FL"')
    start_date = models.DateField("Start of meeting")
    end_date = models.DateField("End of meeting")
    reg_start = models.DateField("Start of early registration")
    early_reg_deadline = models.DateField("End of Early registration",
        help_text="This also marks the beginning of regular registration")
    reg_deadline = models.DateField("End of regular registration")
    paper_submission_start = models.DateTimeField("Start of paper submission")
    paper_submission_end = models.DateTimeField("End of Paper submission end")
    session_submission_start = models.DateTimeField(
        "Start of session submission")
    session_submission_end = models.DateTimeField("End of session submission")
    preliminary_program = models.URLField("Preliminary program URL",
        help_text="If specified, a link to the form will be shown above the "+\
        "session selection section of the registration page.",
        verify_exists=False, blank=True)
    register_form = models.URLField("Registration form URL", blank=True,
        help_text='If specified, a link to the form will be shown at the '+\
        'top of the registration page.', verify_exists=False)

    def __unicode__(self):
        return self.location+" "+unicode(self.start_date.year)

    def registration_active(self):
        """Returns True if today is between registration start and end dates"""
        return self.reg_start <= date.today() <= self.reg_deadline

    def has_registered(self, account):
        """Returns True if given account has a registration for this meeting"""
        return self.registrations.filter(registrant=account).count() > 0

    def can_register(self, account):
        """
        Returns True if today is after or on the start_date and the given
        account hasn't already registered.
        """
        return self.registration_active() and not self.has_registered(account)

    def can_submit_paper(self):
        return (self.paper_submission_start <= datetime.now() <=
                self.paper_submission_end)

    def can_submit_session(self):
        return (self.session_submission_start <= datetime.now() <=
                self.session_submission_end)

    @staticmethod
    def current():
        return Meeting.objects.filter(is_active=1).order_by('-end_date')[0]

    @staticmethod
    def current_or_none():
        """
        Version of Metting.current() that returns None if no meetings
        have been entered.
        """
        try:
            return Meeting.current()
        except IndexError:
            return None

    @staticmethod
    def get_past_meetings(years_ago):
        """
        Returns a Q object which represents all past meetings for the
        past years_ago years
        """
        return Q(start_date__lt=date.today()) &\
            Q(end_date__lt=date.today()) &\
            Q(reg_start__lt=date.today()) &\
            Q(start_date__gte=date(date.today().year - years_ago, 1, 1))

    @meeting_stat
    def get_registration_stats(self):
        """
        Returns list of dictionaries for each registration option, with
        each dictionary containing three entries:
            1) The option name (key="type")
            2) The number of registrations for that option (key="quantity")
            3) Total income from all the above registrations (key="income")
        """
        stats = []
        for opt in self.regoptions.all():
            registrations = Registration.objects.filter(type=opt)
            opt_stats = {
                "type": unicode(opt),
                "quantity": registrations.count(),
                "income": sum(r.get_meeting_cost() for r in registrations),
            }
            stats.append(opt_stats)
        return stats

    def get_registration_time_stats(self):
        """
        Returns list of dictionaries for each registration option, with
        each dictionary containing two entries:
            1) Either "Early", "Regular", or "Onsite" (key="type")
            2) The # of registrations for that time period (key="quantity")
        """
        stats = []
        deadline = datetime.combine(self.early_reg_deadline, time(0))
        regs = self.registrations.all()
        early_regs = regs.filter(date_entered__lte=deadline)
        onsite_regs = regs.filter(date_entered__gte=self.start_date)
        range = (deadline, self.start_date)
        regular_regs = regs.filter(date_entered__range=range)

        period_dict = {
            "Early": early_regs,
            "Regular": regular_regs,
            "Onsite": onsite_regs,
        }
        for period, regs in period_dict.items():
            stats.append({
                "type": period,
                "quantity": regs.count(),
            })
        return stats

    @meeting_stat
    def get_extra_stats(self):
        """
        Returns list of dictionaries for each meeting extra, with
        each dictionary containing three entries:
            1) The extra name (key="type")
            2) The total number of orders for that extra
               from all registrations (key="quantity")
            3) Total income from all the above orders (key="income")
        """
        stats = []
        for xtra in self.extras.all():
            orders = RegistrationExtra.objects.filter(extra=xtra)
            xtra_stats = {
                "type": unicode(xtra.extra_type),
                "quantity": sum(o.quantity for o in orders),
                "income": sum(o.get_total() for o in orders),
            }
            stats.append(xtra_stats)
        return stats

    @meeting_stat
    def get_donation_stats(self):
        """
        Returns list of dictionaries for each meeting donation, with
        each dictionary containing three entries:
            1) The donation name (key="type")
            2) The total number of registration including
               that donation (key="quantity")
            3) Total income from the donations (key="income")
        """
        stats = []
        for obj in self.donations.all():
            donations = RegistrationDonation.objects.filter(donate_type=obj)
            donate_stats = {
                "type": unicode(obj),
                "quantity": donations.count(),
                "income": sum(d.total for d in donations),
            }
            if donate_stats['quantity'] > 0:
                stats.append(donate_stats)
        return stats

    def get_payment_stats(self):
        """
        Returns list of dictionaries for each payment choice, with each
        dictionary containing two entries:
            1) The payment type (key="type")
            2) The total # of registrations that used it (key="quantity")
        """
        stats = []
        regs = self.registrations.all()
        for type in Registration.PAYMENT_TYPES:
            stats.append({
                "type": type[1],
                "quantity": regs.filter(payment_type=type[0]).count(),
            })
        return stats

    def get_session_stats(self):
        """
        Returns list of dictionaries for each accepted session, with each
        dictionary containing two entries:
            1) The session (key="type")
            2) The total # of people who said they'd attend the
               session (key="quantity")
        """
        stats = []
        for sess in self.sessions.filter(accepted=True):
            stats.append({
                "type": sess,
                "quantity": sess.regsessions.count(),
            })
        return stats

    class Meta:
        get_latest_by = "end_date"
        ordering = ['start_date']


class Paper(models.Model):
    AV_CHOICES = (
        ('N', 'None'),
        ('L', 'LCD(PowerPoint)'),
        ('O', 'Overhead Projector'),
    )
    PRIOR_SUNDAY_CHOICES = (
        ('0', 0),
        ('1', 1),
        ('2', 2),
        ('M','More'),
    )
    submitter = models.ForeignKey(user_model, blank=True, null=True)
    presenter_first_name = models.CharField(blank=False, max_length=45)
    presenter_last_name = models.CharField(blank=False, max_length=45)
    presenter_email = models.EmailField(max_length=100)
    title = models.CharField(max_length=300)
    abstract = models.TextField()
    coauthor = models.CharField(max_length=255, blank=True)
    is_poster = models.BooleanField(default=False,
        verbose_name="Is this a poster?")
    av_info = models.CharField(max_length=1, blank=True, choices=AV_CHOICES,
        default='N', verbose_name="Audiovisual Requirement")
    notes = models.TextField(blank=True)
    accepted = models.BooleanField(default=False)
    previous_meetings = models.ManyToManyField(Meeting, blank=True,
        related_name="meeting_papers",
        # only look at past 2 meetings
        limit_choices_to=Meeting.get_past_meetings(2),
        verbose_name="Presented at the following past meetings")
    prior_sundays = models.CharField(default='0', max_length=1, blank=False,
        choices=PRIOR_SUNDAY_CHOICES, verbose_name="How many times over the "+\
        "past 5 years have you been assigned to a Sunday morning slot on "+\
        "the program?")
    creation_time = models.DateTimeField(auto_now_add=True, editable=False)
    sessions = models.ManyToManyField("Session", blank=True, through="SessionPapers")

    def __unicode__(self):
        return self.title

    def get_presenter(self):
        return self.presenter_first_name + " " + self.presenter_last_name

    def send_submission_email(self):
        """
        Sends e-mail notifying submitter of the submission.
        """
        subject = 'Paper Submission Confirmation'
        sender = settings.DJANGO_CONFERENCE_CONTACT_EMAIL
        txt_body = render_to_string("django_conference/submit_paper_email.txt", {
            "paper": self,
        })
        html_body = render_to_string("django_conference/submit_paper_email.html", {
            "paper": self,
        })
        msg = EmailMultiAlternatives(subject=subject, from_email=sender,
            body=txt_body, to=[self.submitter.email])
        msg.attach_alternative(html_body, "text/html")
        msg.send()


class FieldType(models.Model):
    """
    Abstract model for describing a general field on the registration
    form.
    """
    name = models.CharField(max_length=10, primary_key=True,
        help_text="A short, unique name for this field.")
    label = models.CharField(blank=False, max_length=255,
        help_text="Label for this field on the registration page. "+\
        "Enter as HTML.")

    def __unicode__(self):
        # strip out the HTML tags from the label and show that
        return re.sub(r'<[^>]*?>', '', self.label)

    class Meta:
        abstract = True


class ExtraType(FieldType):
    pass


class MeetingExtra(models.Model):
    """
    Model for fixed-price extras (e.g. abstracts) that registrants can
    order while registering.
    """
    meeting = models.ForeignKey(Meeting, related_name="extras")
    extra_type = models.ForeignKey(ExtraType)
    price = models.DecimalField(max_digits=6, decimal_places=2,
        default=0, help_text="The price for one quantity of this extra.")
    help_text = models.CharField(blank=True, max_length=255,
        help_text="Text to be shown next to the extra.")
    max_quantity = models.PositiveIntegerField(default=1,
        help_text="The maximum of this extra that a registrant can order. "+\
        "If set to 1, it will be shown as a checkbox.")
    position = models.PositiveSmallIntegerField(default=1,
        help_text="Used for determining position of the extra on the "+\
        "registration page")

    def __unicode__(self):
        return "%s: %.2f" % (unicode(self.extra_type), self.price)

    class Meta:
        unique_together = ('meeting', 'extra_type')
        ordering = ["meeting", "position"]


class DonationType(FieldType):
    pass


class MeetingDonation(models.Model):
    """
    Model for causes that a registrant can donate to while registering.
    """
    meeting = models.ForeignKey(Meeting, related_name="donations")
    donate_type = models.ForeignKey(DonationType)
    help_text = models.CharField(blank=True, max_length=255,
        help_text="Text to be shown next to the donation input box.")

    def __unicode__(self):
        return unicode(self.donate_type)

    class Meta:
        unique_together = ('meeting', 'donate_type')


class MeetingInstitution(models.Model):
    """Model for institutions that are hosting meetings (HSS, PSA, etc.)"""
    meeting = models.ForeignKey(Meeting, related_name='institutions')
    acronym = models.CharField(max_length=4, blank=False)
    name = models.CharField(max_length=45, blank=False)

    def __unicode__(self):
        return self.acronym

    class Meta:
        ordering = ["name"]


class RegistrationOption(models.Model):
    """Model for storing the options and prices for people registering"""
    ADMIN_ONLY_HELP = "If checked, this option will only be available "+\
                      "when registering through the admin interface."
    meeting = models.ForeignKey(Meeting, related_name="regoptions")
    option_name = models.CharField(max_length=30, blank=False)
    early_price = models.DecimalField(max_digits=5, decimal_places=2)
    regular_price = models.DecimalField(max_digits=5, decimal_places=2)
    onsite_price = models.DecimalField(max_digits=5, decimal_places=2)
    admin_only = models.BooleanField(default=False, help_text=ADMIN_ONLY_HELP)

    def __unicode__(self):
        return self.option_name

    class Meta:
        ordering = ["-meeting", "option_name", "regular_price"]
        unique_together = ("meeting", "option_name")


class Registration(models.Model):
    """Model to store registrations"""
    PAYMENT_TYPES = (
        ("na", "Not Applicable"),
        ("cc", "Credit Card"),
        ("ch", "Check"),
        ("ca", "Cash"),
        ("mo", "Money Order"),
    )
    meeting = models.ForeignKey(Meeting, related_name='registrations',
        default=Meeting.current_or_none())
    type = models.ForeignKey(RegistrationOption,
        limit_choices_to={'meeting': Meeting.current_or_none()})
    special_needs = models.TextField(blank=True)
    date_entered = models.DateTimeField()
    payment_type = models.CharField(max_length=2, choices=PAYMENT_TYPES,
        default="cc")
    registrant = models.ForeignKey(user_model, related_name="registrations")
    entered_by = models.ForeignKey(user_model,
        limit_choices_to={'is_staff': True})
    sessions = models.ManyToManyField("Session", blank=True,
        related_name="regsessions",
        limit_choices_to={'meeting': Meeting.current_or_none(),
                          'accepted': True})

    def __unicode__(self):
        return self.registrant.get_full_name()+": "+unicode(self.date_entered)

    def save(self):
        if not self.id:
            self.date_entered = datetime.now()
        super(Registration, self).save()

    def get_meeting_cost(self):
        """Calculates total cost for the meeting registration only
           (i.e. without banquets, abstracts, donations added in)"""
        #if we're past the early reg deadline, charge regular price
        if self.date_entered.date() > self.meeting.start_date:
            cost = self.type.onsite_price
        elif self.date_entered.date() <= self.meeting.early_reg_deadline:
            cost = self.type.early_price
        else:
            cost = self.type.regular_price
        return Decimal(cost)

    def get_total(self):
        """Calculates the total cost for this registration"""
        total = self.get_meeting_cost()
        total += sum(e.get_total() for e in self.regextras.all())
        total += sum(d.total for d in self.regdonations.all())
        return total

    def send_register_email(self):
        """
        Sends e-mail to registrant with registration details. E-mail will
        contain both an HTML and text version.
        """
        subject = unicode(self.meeting.start_date.year)+" Meeting Registration"
        text = render_to_string("django_conference/register_email.html", {
            "meeting": self.meeting,
            "registration": self,
        })
        sender = settings.DJANGO_CONFERENCE_CONTACT_EMAIL
        msg = EmailMessage(subject=subject, body=text,
            from_email=sender, to=[self.registrant.email])
        msg.send()

    def has_special_needs(self):
        """
        Return True if this registration entered anything for the
        "Special Needs" field, False otherwise
        """
        return len(self.special_needs) > 0
    has_special_needs.short_description = "Has Special Needs"
    has_special_needs.boolean = True
    has_special_needs.admin_order_field = 'special_needs'

    class Meta:
        get_latest_by = "date_entered"
        ordering = ["-meeting", "registrant"]


class RegistrationExtra(models.Model):
    registration = models.ForeignKey(Registration, related_name="regextras")
    extra = models.ForeignKey(MeetingExtra,
        limit_choices_to={'meeting': Meeting.current_or_none()})
    quantity = models.PositiveIntegerField()
    # allow price to be NULL, which indicates we should use extra.price instead
    price = models.DecimalField("Price override", max_digits=6,
        null=True, blank=True, decimal_places=2)

    def get_total(self):
        price = self.price if self.price is not None else self.extra.price
        return Decimal(self.quantity * price)

    def is_price_override(self):
        """
        Returns True if price has been overriden from default price in
        extra.price, False otherwise
        """
        return self.price is not None and self.price != self.extra.price

    def __unicode__(self):
        return unicode(self.extra.extra_type)

    def registrant_email(self):
        return self.registration.registrant.email

    class Meta:
        unique_together = ('registration', 'extra')


class RegistrationGuest(models.Model):
    """
    Represents guests the registrant is bringing.
    """
    registration = models.ForeignKey(Registration, related_name="guests")
    first_name = models.CharField(blank=False, max_length=45)
    last_name = models.CharField(blank=False, max_length=45)

    def __unicode__(self):
        return self.first_name + " " + self.last_name


class RegistrationDonation(models.Model):
    registration = models.ForeignKey(Registration,
        related_name="regdonations")
    donate_type = models.ForeignKey(MeetingDonation,
        limit_choices_to={'meeting': Meeting.current_or_none()})
    total = models.DecimalField(max_digits=6, decimal_places=2)

    def __unicode__(self):
        return unicode(self.donate_type)

    class Meta:
        ordering = ['-registration', 'donate_type']


class SessionCadre(models.Model):
    """
    Model for people involved in organizing, commentating on, or chairing
    sessions.
    """
    GENDERS = (
        ('O', 'Other'),
        ('M', 'Male'),
        ('F', 'Female'),
    )
    TYPES = (
        ('O', 'Other'),
        ('F', 'Faculty Member'),
        ('I', 'Independent Scholar'),
        ('G', 'Graduate Student'),
        ('A', 'Administrator'),
        ('P', 'Post-Doctoral Fellow'),
        ('H', 'Public Historian'),
    )
    first_name = models.CharField(max_length=30)
    mi = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30)
    gender = models.CharField(max_length=1, choices=GENDERS, default='O')
    type = models.CharField(max_length=1, choices=TYPES, default='O')
    email = models.EmailField(max_length=100)
    institution = models.CharField(max_length=100)

    def __unicode__(self):
        return u"%s %s, %s (%s)" % (self.first_name, self.last_name,
            self.institution, self.gender)

    def get_full_name(self):
        if self.mi:
            return "%s %s %s" % (self.first_name, self.mi, self.last_name)
        return "%s %s" % (self.first_name, self.last_name)

    class Meta:
        verbose_name_plural = "Session cadre"


class Session(models.Model):
    submitter = models.ForeignKey(user_model, blank=True, null=True)
    meeting = models.ForeignKey(Meeting, related_name="sessions",
        default=Meeting.current_or_none())
    start_time = models.DateTimeField(blank=True, null=True)
    stop_time = models.DateTimeField(blank=True, null=True)
    room_no = models.CharField(max_length=30, blank=True, null=True)
    title = models.CharField(max_length=300)
    notes = models.TextField(blank=True)
    abstract = models.TextField(blank=True)
    creation_time = models.DateTimeField(auto_now_add=True, editable=False)
    accepted = models.BooleanField(default=False)
    chairs = models.ManyToManyField(SessionCadre, null=True, blank=True,
        related_name="sessions_chaired")
    organizers = models.ManyToManyField(SessionCadre, blank=True,
        related_name="sessions_organized")
    commentators = models.ManyToManyField(SessionCadre, blank=True,
        related_name="sessions_commentated")
    papers = models.ManyToManyField("Paper", blank=True, through="SessionPapers")

    def __unicode__(self):
        return self.title

    def enumerate_papers(self):
        """
        Returns enumerator for the papers associated with this session
        """
        return enumerate(self.papers.all()
            .order_by('submitter__last_name', 'submitter__first_name'))

    def get_time_slot_string(self):
        # If both the starting and ending times are on the same day,
        # then use the format "Sunday, 07:00-07:45 PM", else use
        # "Sunday 07:00 PM - Monday 01:00 AM"
        if self.start_time.day == self.stop_time.day:
            return u"%s-%s" % (
                self.start_time.strftime("%A, %I:%M"),
                self.stop_time.strftime("%I:%M %p"))
        else:
            format = "%A %I:%M %p"
            return u"%s - %s" % (
                self.start_time.strftime(format),
                self.stop_time.strftime(format))

    def send_submission_email(self):
        """
        Sends e-mail notifying organizer(s) of the submission.
        """
        subject = 'Session Submission Confirmation'
        sender = settings.DJANGO_CONFERENCE_CONTACT_EMAIL
        body = render_to_string("django_conference/submit_session_email.txt",
            {"session": self})
        msg = EmailMessage(subject=subject, from_email=sender,
            body=body, to=[o.email for o in self.organizers.all()])
        msg.send()

    def save(self):
        """
        When a session is saved, all papers should have their "accepted" field
        adjusted accordingly
        """
        super(Session, self).save()
        for paper in self.papers.all():
            paper.accepted = self.accepted
            paper.save()

    class Meta:
        ordering = ['-meeting', 'start_time', 'stop_time']


class SessionPapers(models.Model):
    session = models.ForeignKey(Session)
    paper = models.ForeignKey(Paper)
    position = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return "session paper #%i" % self.position
