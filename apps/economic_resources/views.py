from datetime import date
from datetime import datetime, timedelta
from itertools import chain
from operator import attrgetter


from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_app
from django.db.models import Q

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from pinax.utils.importlib import import_module

from tagging.models import Tag
from django.utils.translation import ugettext

from economic_resources.models import EconomicResource
from economic_resources.forms import EconomicResourceForm, EditEconomicResourceForm

# todo: notifications
#try:
#    notification = get_app('notification')
#except ImproperlyConfigured:
#    notification = None

notification = None

def economic_resources(request, group_slug=None, template_name="economic_resources/economic_resource_list.html", bridge=None):
    
    group_type = ""
    if bridge:
        try:
            group = bridge.get_group(group_slug)
            group_type = group._meta.verbose_name.title()
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        if group:
            is_member = group.user_is_member(request.user)
        else:
            is_member = True
    
    group_by = request.GET.get("group_by")
    
    if group:
        economic_resources = group.content_objects(EconomicResource)
        group_base = bridge.group_base_template()
    else:
        economic_resources = EconomicResource.objects.filter(object_id=None)
        group_base = None   
    
    return render_to_response(template_name, {
        "group": group,
        "group_type": group_type,
        "is_member": is_member,
        "group_base": group_base,
        "economic_resources": economic_resources,
    }, context_instance=RequestContext(request))


def add_economic_resource(request, group_slug=None, secret_id=None, form_class=EconomicResourceForm, template_name="economic_resources/add.html", bridge=None):
    
    group_type = ""
    if bridge:
        try:
            group = bridge.get_group(group_slug)
            group_type = group._meta.verbose_name.title()
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if group:
        group_base = bridge.group_base_template()
    else:
        group_base = None
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        if group:
            is_member = group.user_is_member(request.user)
        else:
            is_member = True
    
    if request.method == "POST":
        if request.user.is_authenticated():
            economic_resource_form = form_class(request.user, group, request.POST)
            if economic_resource_form.is_valid():
                economic_resource = economic_resource_form.save(commit=False)
                economic_resource.creator = request.user
                economic_resource.group = group
                economic_resource.save()
                request.user.message_set.create(message="added economic_resource '%s'" % economic_resource.name)
                if notification:
                    if group:
                        notify_list = group.member_queryset()
                    else:
                        notify_list = User.objects.all() # @@@
                    notify_list = notify_list.exclude(id__exact=request.user.id)
                    notification.send(notify_list, "economic_resources_new", {"creator": request.user, "economic_resource": economic_resource, "group": group})
                if request.POST.has_key('add-another-economic_resource'):
                    if group:
                        redirect_to = bridge.reverse("economic_resource_add", group)
                    else:
                        redirect_to = reverse("economic_resource_add")
                    return HttpResponseRedirect(redirect_to)
                if group:
                    redirect_to = bridge.reverse("economic_resource_list", group)
                else:
                    redirect_to = reverse("economic_resource_list")
                return HttpResponseRedirect(redirect_to)
    else:
        economic_resource_form = form_class(request.user, group)
    
    return render_to_response(template_name, {
        "group": group,
        "group_type": group_type,
        "is_member": is_member,
        "economic_resource_form": economic_resource_form,
        "group_base": group_base,
    }, context_instance=RequestContext(request))


def economic_resource(request, id, group_slug=None, template_name="economic_resources/economic_resource.html", bridge=None):
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if group:
        economic_resources = group.content_objects(EconomicResource)
        group_base = bridge.group_base_template()
    else:
        economic_resources = EconomicResource.objects.filter(object_id=None)
        group_base = None
    
    economic_resource = get_object_or_404(economic_resources, id=id)
    
    if group:
        notify_list = group.member_queryset()
    else:
        notify_list = User.objects.all()
    notify_list = notify_list.exclude(id__exact=request.user.id)
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        if group:
            is_member = group.user_is_member(request.user)
        else:
            is_member = True
    
    if is_member and request.method == "POST":
        form = EditEconomicResourceForm(request.user, group, request.POST, instance=economic_resource)
        if form.is_valid():
            economic_resource = form.save()
            if "tags" in form.changed_data:
                request.user.message_set.create(message="updated tags on the economic_resource")
                if notification:
                    notification.send(notify_list, "economic_resources_tags", {"user": request.user, "economic_resource": economic_resource, "group": group})
            form = EditEconomicResourceForm(request.user, group, instance=economic_resource)
    else:
        form = EditEconomicResourceForm(request.user, group, instance=economic_resource)
    
    return render_to_response(template_name, {
        "group": group,
        "economic_resource": economic_resource,
        "is_member": is_member,
        "form": form,
        "group_base": group_base,
    }, context_instance=RequestContext(request))


