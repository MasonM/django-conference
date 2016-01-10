from django.http import HttpResponseNotFound
from django.conf.urls.defaults import *


handler404 = lambda request: HttpResponseNotFound()

urlpatterns = patterns('',
    (r'^account/', 'django.contrib.auth.views.login', {
        'template_name': 'admin/login.html'
    }),
    (r'^conference/', include('django_conference.urls')),
)
