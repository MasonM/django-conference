from django.core.urlresolvers import reverse
from django.contrib import admin
from django.conf import settings
from django import forms

from django_conference.models import (DonationType, ExtraType, Meeting,
    MeetingDonation, MeetingExtra, MeetingInstitution, Paper, PaperPresenter,
    Registration, RegistrationDonation, RegistrationExtra, RegistrationGuest,
    RegistrationOption, Session, SessionCadre, SessionPapers,
    PaperPresenterRegion, PaperPresenterTimePeriod, PaperPresenterSubject)

from dal import autocomplete


admin.site.register(DonationType)
admin.site.register(ExtraType)


class MeetingExtraInline(admin.StackedInline):
    model = MeetingExtra
    extra = 1
    introduction = """
        Enter any fixed-price extras (e.g. abstracts) that registrants should
        be able to order. Note that registrants can not change the price
        for an extra, but it can be overriden on a per-registration basis in
        the admin interface.
    """
class MeetingDonationInline(admin.StackedInline):
    model = MeetingDonation
    extra = 1
    introduction = """
        Enter any causes that registrants should be able to donate to
        while registering.
    """
class MeetingInstitutionInline(admin.TabularInline):
    model = MeetingInstitution
    extra = 1
    introduction = """
        Enter the institutions associated with this meeting.
        The acronyms will be used to identify the meeting.
    """
class RegistrationOptionInline(admin.TabularInline):
    model = RegistrationOption
    extra = 1
    introduction = """
        Enter the registration types here. Registrants will be required to
        to select one of these options while registering. <br/>
        If the "Admin Only" checkbox is checked, then the associated option
        will only be available when entering registrations through the admin
        interface.
    """
class MeetingAdmin(admin.ModelAdmin):
    change_form_template = "django_conference/meeting_change_form.html"
    fieldsets = (
       ("Location and General Information", {
           'fields': ('location', 'start_date', 'end_date', 'is_active'),
       }),
       ("Registration Information", {
           'fields': ('reg_start', 'early_reg_deadline', 'reg_deadline'),
       }),
       ("Paper/Session Information", {
           'fields': ('paper_submission_start', 'paper_submission_end',
               'session_submission_start', 'session_submission_end'),
       }),
       ("Links", {
           'fields': ('register_form', 'preliminary_program'),
       }),
    )
    inlines = [MeetingDonationInline, MeetingExtraInline,
        MeetingInstitutionInline, RegistrationOptionInline]
    actions = '<a href="%s">Admin Tasks</a>'
    list_display = ('__unicode__', 'admin_actions')

    def admin_actions(self, obj):
        view_name = 'django_conference_choose_admin_task'
        return self.actions % reverse(view_name, kwargs={'meeting_id': obj.pk})
    admin_actions.short_description = "Administrative Actions"
    admin_actions.allow_tags = True

    class Media:
        js = [settings.STATIC_URL+"django_conference/js/jquery-1.3.2.min.js",
              settings.STATIC_URL+"django_conference/js/dynamic_inlines.js"]
admin.site.register(Meeting, MeetingAdmin)


class LimitChoicesForFieldsToCurrentMeetingMixin(object):
    """
    Mixin to modify fields that reference a meeting-related model in the
    ModelForm used to display model. Iterates over the
    self.limit_to_curr_meeting list to limit the choices for the given fields
    to the current meeting.

    For example, this allows the RegistrationAdmin form to only show
    registration options that apply to the meeting associated with the
    registration. Without this, the "type" drop-down would show every
    registration option, which would be impossible to use.
    """
    def update_form_to_limit_choices(self, form, obj):
        for field_to_limit in self.limit_to_curr_meeting:
            choices = getattr(obj.meeting,
                field_to_limit['relationship_attribute'])
            additional_filter = field_to_limit.get('filter', None)
            if additional_filter: choices = choices.filter(**additional_filter)
            field_name = field_to_limit['field_name']
            form.base_fields[field_name].queryset = choices

    def get_form(self, request, obj=None, **kwargs):
        # This is for classes that inherit from admin.ModelAdmin
        form = super(LimitChoicesForFieldsToCurrentMeetingMixin,
            self).get_form(request, obj, **kwargs)
        if obj: self.update_form_to_limit_choices(form, obj)
        return form

    def get_formset(self, request, obj=None, **kwargs):
        # This is for classes that inherit from admin.InlineModelAdmin
        formset = super(LimitChoicesForFieldsToCurrentMeetingMixin,
            self).get_formset(request, obj, **kwargs)
        if obj: self.update_form_to_limit_choices(formset.form, obj)
        return formset


class RegistrationExtraInline(
    LimitChoicesForFieldsToCurrentMeetingMixin, admin.TabularInline):
    model = RegistrationExtra
    num = 4
    limit_to_curr_meeting = [{
        'field_name': 'extra',
        'relationship_attribute': 'extras',
    }]
class RegistrationDonationInline(
    LimitChoicesForFieldsToCurrentMeetingMixin, admin.TabularInline):
    model = RegistrationDonation
    extra = 3
    limit_to_curr_meeting = [{
        'field_name': 'donate_type',
        'relationship_attribute': 'donations',
    }]
class RegistrationGuestInline(admin.TabularInline):
    model = RegistrationGuest
    extra = 1
class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Paper
        fields = '__all__'
        widgets = {
            'registrant': autocomplete.ModelSelect2(url='user-autocomplete'),
        }
class RegistrationAdmin(
    LimitChoicesForFieldsToCurrentMeetingMixin, admin.ModelAdmin):
    form = RegistrationForm
    date_hierarchy = "date_entered"
    fieldsets = (
        ("General Information", {
            'fields': ('registrant', 'type', 'entered_by', 'meeting',
                       'payment_type'),
        }),
        ("Special Information", {
            'fields': ('special_needs', 'sessions'),
        }),
    )
    list_display = ('registrant', 'meeting', 'type', 'date_entered',
        'has_special_needs')
    search_fields = ('registrant__first_name', 'registrant__last_name',
        'type__option_name', 'special_needs')
    inlines = [RegistrationExtraInline, RegistrationDonationInline,
        RegistrationGuestInline]
    filter_horizontal = ['sessions']
    limit_to_curr_meeting = [
        { 'field_name': 'type', 'relationship_attribute': 'regoptions' },
        {
            'field_name': 'sessions',
            'relationship_attribute': 'sessions',
            'filter': { 'accepted': True },
        },
    ]
admin.site.register(Registration, RegistrationAdmin)


class SessionCadreAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'gender', 'institution', 'email')
    search_fields = ['last_name', 'first_name', 'institution', 'email']
    ordering = ['last_name', 'first_name']
admin.site.register(SessionCadre, SessionCadreAdmin)


class SessionPapersForm(forms.ModelForm):
    class Meta:
        model = SessionPapers
        fields = '__all__'
        widgets = {
            'paper': autocomplete.ModelSelect2(url='paper-autocomplete'),
        }
class SessionPapersInline(admin.TabularInline):
    form = SessionPapersForm
    model = SessionPapers
    extra = 3


class PaperForm(forms.ModelForm):
    class Meta:
        model = Paper
        fields = '__all__'
        widgets = {
            'presenter': autocomplete.ModelSelect2(
                url='paper-presenter-autocomplete'),
            'submitter': autocomplete.ModelSelect2(url='user-autocomplete'),
        }
class PaperAdmin(admin.ModelAdmin):
    form = PaperForm
    fieldsets = [
        (None, {'fields': ['title', 'abstract', 'submitter',
            'presenter', 'accepted']}),
        ('Additional Info', {
            'fields': ['coauthor', 'is_poster', 'av_info', 'notes',
                'prior_sundays', 'previous_meetings'],
        }),
    ]
    list_display = ('title', 'submitter', 'presenter', 'is_poster', 'accepted',
        'av_info', 'creation_time')
    inlines = [SessionPapersInline]
    list_filter = ['accepted', 'is_poster']
    search_fields = ['title', 'presenter__first_name', 'presenter__last_name',
        'presenter__email', 'notes', 'submitter__first_name',
        'submitter__last_name', 'submitter__email', 'abstract', 'coauthor']
    date_hierarchy = 'creation_time'
    filter_horizontal = ['previous_meetings']
    ordering = ['title']
admin.site.register(Paper, PaperAdmin)


class PaperPresenterAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
admin.site.register(PaperPresenter, PaperPresenterAdmin)

admin.site.register(PaperPresenterTimePeriod)
admin.site.register(PaperPresenterRegion)
admin.site.register(PaperPresenterSubject)


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = '__all__'
        widgets = {
            'submitter': autocomplete.ModelSelect2(url='user-autocomplete'),
        }
class SessionAdmin(admin.ModelAdmin):
    form = SessionForm
    fieldsets = [
        (None, {
            'fields': ['meeting', 'title', 'abstract', 'accepted'],
        }),
        ('People', {
            'fields': ['submitter', 'chairs', 'organizers', 'commentators']
        }),
        ('Additional Info', {
            'fields': ['room_no', 'start_time', 'stop_time', 'notes']
        }),
    ]
    search_fields = ('title', 'abstract', 'notes', 'chairs__first_name',
        'chairs__last_name', 'chairs__institution',
        'submitter__first_name', 'submitter__last_name')
    ordering = ['title']
    inlines = [SessionPapersInline]
    filter_horizontal = ['chairs', 'organizers', 'commentators']
    list_display = ('title', 'submitter', 'meeting', 'accepted',
        'get_chair_string', 'start_time', 'stop_time', 'creation_time')
    list_filter = ['meeting', 'accepted']

    def get_chair_string(self, obj):
        return ', '.join(chair.get_full_name() for chair in obj.chairs.all())
    get_chair_string.short_description = "Chairs"
admin.site.register(Session, SessionAdmin)
