from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('',
    (r'^conference/', include('django_conference.urls')),
    (r'^accounts/login/', 'django.contrib.auth.views.login', {
        'template_name': 'admin/login.html'
    }),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
    }),
)
