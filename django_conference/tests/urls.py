from django.conf.urls.defaults import *


urlpatterns = patterns('',
    (r'^account/', 'django.contrib.auth.views.login', {
        'template_name': 'admin/login.html'
    }),
    (r'^conference/', include('django_conference.urls')),
)
