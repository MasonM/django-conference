from django.core.urlresolvers import reverse
from django.contrib import admin

from django_conference import settings
from django_conference.models import (DonationType, ExtraType, Meeting,
    MeetingDonation, MeetingExtra, MeetingInstitution, Paper, Registration,
    RegistrationDonation, RegistrationExtra, RegistrationGuest,
    RegistrationOption, Session, SessionCadre)


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
           'fields': ('location', 'start_date', 'end_date'),
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
        js = [settings.DJANGO_CONFERENCE_MEDIA_ROOT+"/js/jquery-1.3.2.min.js",
              settings.DJANGO_CONFERENCE_MEDIA_ROOT+"/js/dynamic_inlines.js"]
admin.site.register(Meeting, MeetingAdmin)


class RegistrationExtraInline(admin.TabularInline):
    model = RegistrationExtra
    num = 4
class RegistrationDonationInline(admin.TabularInline):
    model = RegistrationDonation
    extra = 3
class RegistrationGuestInline(admin.TabularInline):
    model = RegistrationGuest
    extra = 1
class RegistrationAdmin(admin.ModelAdmin):
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
admin.site.register(Registration, RegistrationAdmin)


class SessionCadreAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'institution', 'email')
    search_fields = ['last_name', 'first_name', 'institution', 'email']
    ordering = ['last_name', 'first_name']
admin.site.register(SessionCadre, SessionCadreAdmin)


class PaperAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title', 'abstract', 'presenter', 'accepted']}),
        ('Additional Info', {
            'fields': ['coauthor', 'is_poster', 'av_info', 'notes',
                       'previous_meetings', 'sessions'],
        }),
    ]
    list_display = ('title', 'presenter', 'is_poster', 'accepted',
        'av_info', 'creation_time')
    list_filter = ['accepted', 'is_poster']
    search_fields = ['title', 'presenter__first_name', 'presenter__last_name',
        'presenter__email', 'abstract', 'notes', 'coauthor']
    date_hierarchy = 'creation_time'
    filter_horizontal = ['previous_meetings', 'sessions']
    ordering = ['title']
admin.site.register(Paper, PaperAdmin)


class SessionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {
            'fields': ['meeting', 'title', 'abstract', 'accepted'],
        }),
        ('People', {
            'fields': ['chairs', 'organizers', 'commentators']
        }),
        ('Additional Info', {
            'fields': ['room_no', 'start_time', 'stop_time', 'notes',
                       'papers']
        }),
    ]
    search_fields = ('title', 'abstract', 'notes', 'papers__title',
        'papers__abstract', 'papers__coauthor', 'papers__notes',
        'chairs__first_name', 'chairs__last_name', 'chairs__institution')
    ordering = ['title']
    filter_horizontal = ['papers', 'chairs', 'organizers', 'commentators']
    list_display = ('title', 'meeting', 'accepted', 'get_chair_string',
        'start_time', 'stop_time', 'creation_time')
    list_filter = ['meeting', 'accepted']

    def get_chair_string(self, obj):
        return ', '.join(chair.get_full_name() for chair in obj.chairs.all())
    get_chair_string.short_description = "Chairs"
admin.site.register(Session, SessionAdmin)
