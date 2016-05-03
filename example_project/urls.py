from django.conf.urls import *
from django.contrib import admin


admin.autodiscover()


urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^admin_docs/', include('django.contrib.admindocs.urls')),
    (r'^conference/', include('django_conference.urls')),
    (r'^accounts/login/', 'django.contrib.auth.views.login', {
        'template_name': 'admin/login.html'
    }),
)
