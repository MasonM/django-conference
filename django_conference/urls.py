from django.conf.urls import *
from django.views.generic import TemplateView

from django_conference import views, autocomplete, admin_tasks


urlpatterns = patterns('',
    # Paper submission/editing
    url(r'^submit_paper',
        views.submit_paper,
        name="django_conference_submit_paper"),
    url(r'^edit_paper/(?P<paper_id>\d+)',
        views.edit_paper,
        name="django_conference_edit_paper"),
    url(r'^submit_success/(?P<id>\d+)/',
        views.submission_success,
        name="django_conference_submission_success"),

    # Session submission
    url(r'^submit_session_papers',
        views.submit_session_papers,
        name="django_conference_submit_session_papers"),
    url(r'^submit_session',
        views.submit_session,
        name="django_conference_submit_session"),

    # Meeting registration
    url(r'^payment/(?P<reg_id>\d+)?',
        views.payment,
        name="django_conference_payment"),
    url(r'^register_success',
        TemplateView.as_view(template_name=
            'django_conference/register_success.html'),
        name="django_conference_register_success"),
    url(r'^register',
        views.register,
        name="django_conference_register"),
    url(r'^paysuccess',
        TemplateView.as_view(template_name=
            'django_conference/pay_success.html'),
        name="django_conference_paysuccess"),

    # Admin
    url(r'^choose_admin_task/(?P<meeting_id>\d+)',
        admin_tasks.choose_task,
        name="django_conference_choose_admin_task"),
    url(r'^do_admin_task/(?P<meeting_id>\d+)/(?P<task_id>\d+)',
        admin_tasks.do_task,
        name="django_conference_do_admin_task"),
    url(r'^paper-presenter-autocomplete/$',
        autocomplete.PaperPresenterAutocomplete.as_view(),
        name='paper-presenter-autocomplete'),
    url(r'^user-autocomplete/$',
        autocomplete.UserAutocomplete.as_view(),
        name='user-autocomplete'),
    url(r'^paper-autocomplete/$',
        autocomplete.PaperAutocomplete.as_view(),
        name='paper-autocomplete'),

    # Homepage
    url(r'',
        views.homepage,
        name="django_conference_home"),
)
