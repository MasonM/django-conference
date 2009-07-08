from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

import views
import admin_tasks


urlpatterns = patterns('',
    url(r'edit_paper/(?P<paper_id>\d+)/',
        views.edit_paper,
        name="django_conference_edit_paper"),
    url(r'submit_paper',
        views.submit_paper,
        name="django_conference_submit_paper"),
    url(r'submit_session',
        views.submit_session,
        name="django_conference_submit_session"),
    url(r'^submit_success/(?P<id>\d+)/',
        views.submission_success,
        name="django_conference_submission_success"),
    url(r'^register_success',
        direct_to_template,
        {'template': 'django_conference/register_success.html'},
        name="django_conference_register_success"),
    url('^paysuccess',
        direct_to_template,
        {'template': 'django_conference/pay_success.html'},
        name="django_conference_paysuccess"),
    url(r'^payment/(?P<reg_id>\d+)?',
        views.payment,
        name="django_conference_payment"),
    url(r'^choose_admin_task/(?P<meeting_id>\d+)',
        admin_tasks.choose_task,
        name="django_conference_choose_admin_task"),
    url(r'^do_admin_task/(?P<meeting_id>\d+)/(?P<task_id>\d+)',
        admin_tasks.do_task,
        name="django_conference_do_admin_task"),
    url(r'register',
        views.register,
        name="django_conference_register"),
    url(r'',
        views.homepage,
        name="django_conference_home"),
)
