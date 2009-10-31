from django.conf.urls.defaults import *

urlpatterns = patterns('',
        url(r'^$', 'economic_events.views.economic_events', name="economic_event_list"),
        url(r'^give/$', 'economic_events.views.add_give_economic_event', name="economic_event_give"),
        #url(r'^take/$', 'economic_events.views.add_take_economic_event', name="economic_event_take"),
        url(r'^economic_event/(?P<id>\d+)/$', 'economic_events.views.economic_event', name="economic_event_detail"),

    )
