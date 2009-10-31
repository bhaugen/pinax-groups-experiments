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

from economic_events.models import EconomicAgent, EconomicEvent
from economic_events.forms import GiveEconomicEventForm, TakeEconomicEventForm, EditEconomicEventForm

# todo: notifications
#try:
#    notification = get_app('notification')
#except ImproperlyConfigured:
#    notification = None

notification = None

def economic_events(request, group_slug=None, template_name="economic_events/economic_event_list.html", bridge=None):
    
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
    
    give_events = []
    take_events = []
    economic_events = []

    if group:
        agent = EconomicAgent.objects.agent_for_object(group)
        give_events = EconomicEvent.objects.filter(from_agent=agent)
        take_events = EconomicEvent.objects.filter(to_agent=agent)
        group_base = bridge.group_base_template()
    else:
        economic_events = EconomicEvent.objects.filter(object_id=None)
        group_base = None   
    
    return render_to_response(template_name, {
        "group": group,
        "group_type": group_type,
        "is_member": is_member,
        "group_base": group_base,
        "give_events": give_events,
        "take_events": take_events,
        "economic_events": economic_events,
    }, context_instance=RequestContext(request))


def add_give_economic_event(request, group_slug=None, secret_id=None, form_class=GiveEconomicEventForm, template_name="economic_events/add.html", bridge=None):
    
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
            economic_event_form = form_class(request.user, group, request.POST)
            if economic_event_form.is_valid():
                economic_event = economic_event_form.save(commit=False)
                economic_event.creator = request.user
                data = economic_event_form.cleaned_data
                resource = data["resource"]
                to_agent = data["to_agent"]
                resource.group = to_agent.group
                resource.save()
                economic_event.save()
                request.user.message_set.create(message="added economic_event '%s'" % economic_event)
                if notification:
                    if group:
                        notify_list = group.member_queryset()
                    else:
                        notify_list = User.objects.all() # @@@
                    notify_list = notify_list.exclude(id__exact=request.user.id)
                    notification.send(notify_list, "economic_events_new", {"creator": request.user, "economic_event": economic_event, "group": group})
                if request.POST.has_key('add-another-economic_event'):
                    if group:
                        redirect_to = bridge.reverse("economic_event_give", group)
                    else:
                        redirect_to = reverse("economic_event_give")
                    return HttpResponseRedirect(redirect_to)
                if group:
                    redirect_to = bridge.reverse("economic_event_list", group)
                else:
                    redirect_to = reverse("economic_event_list")
                return HttpResponseRedirect(redirect_to)
    else:
        economic_event_form = form_class(request.user, group)
    
    return render_to_response(template_name, {
        "group": group,
        "group_type": group_type,
        "is_member": is_member,
        "economic_event_form": economic_event_form,
        "group_base": group_base,
    }, context_instance=RequestContext(request))


def economic_event(request, id, group_slug=None, template_name="economic_events/economic_event.html", bridge=None):
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if group:
        economic_events = group.content_objects(EconomicEvent)
        group_base = bridge.group_base_template()
    else:
        economic_events = EconomicEvent.objects.filter(object_id=None)
        group_base = None
    
    economic_event = get_object_or_404(economic_events, id=id)
    
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
        form = EditEconomicEventForm(request.user, group, request.POST, instance=economic_event)
        if form.is_valid():
            economic_event = form.save()
            if "tags" in form.changed_data:
                request.user.message_set.create(message="updated tags on the economic_event")
                if notification:
                    notification.send(notify_list, "economic_events_tags", {"user": request.user, "economic_event": economic_event, "group": group})
            form = EditEconomicEventForm(request.user, group, instance=economic_event)
    else:
        form = EditEconomicEventForm(request.user, group, instance=economic_event)
    
    return render_to_response(template_name, {
        "group": group,
        "economic_event": economic_event,
        "is_member": is_member,
        "form": form,
        "group_base": group_base,
    }, context_instance=RequestContext(request))


