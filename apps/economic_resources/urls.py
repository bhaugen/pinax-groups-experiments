from django.conf.urls.defaults import *

urlpatterns = patterns('',
        url(r'^$', 'economic_resources.views.economic_resources', name="economic_resource_list"),
        url(r'^add/$', 'economic_resources.views.add_economic_resource', name="economic_resource_add"),
        url(r'^economic_resource/(?P<id>\d+)/$', 'economic_resources.views.economic_resource', name="economic_resource_detail"),

    )
