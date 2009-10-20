from django.conf.urls.defaults import *

from company.models import Company

from groups.bridge import ContentBridge


bridge = ContentBridge(Company, 'company')

urlpatterns = patterns('company.views',
    url(r'^$', 'companies', name="company_list"),
    url(r'^create/$', 'create', name="company_create"),
    url(r'^your_companies/$', 'your_companies', name="your_companies"),
    # company-specific
    url(r'^company/(?P<group_slug>[-\w]+)/$', 'company', name="company_detail"),
    url(r'^company/(?P<group_slug>[-\w]+)/delete/$', 'delete', name="company_delete"),
)

urlpatterns += bridge.include_urls('topics.urls', r'^company/(?P<group_slug>[-\w]+)/topics/')
urlpatterns += bridge.include_urls('economic_resources.urls', r'^company/(?P<group_slug>[-\w]+)/resources/')
urlpatterns += bridge.include_urls('wiki.urls', r'^company/(?P<group_slug>[-\w]+)/wiki/')
urlpatterns += bridge.include_urls('projects.urls', r'^company/(?P<parent_slug>[-\w]+)/projects/')
