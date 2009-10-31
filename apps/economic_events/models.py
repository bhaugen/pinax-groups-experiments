from datetime import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from economic_resources.models import EconomicResource

from tagging.fields import TagField
from tagging.models import Tag

class EconomicAgentManager(models.Manager):

    def _generate_object_kwarg_dict(self, content_object, **kwargs):
        """
        Generates the most comment keyword arguments for a given ``content_object``.
        """
        kwargs['content_type'] = ContentType.objects.get_for_model(content_object)
        kwargs['object_id'] = getattr(content_object, 'pk', getattr(content_object, 'id'))
        return kwargs

	# todo: maybe delete, already done by group.content_objects
    def agent_for_object(self, content_object, **kwargs):
        """
        gets or creates the EconomicAgent for the given ``content_object``.
        """
        agent, created = self.get_or_create(**self._generate_object_kwarg_dict(content_object, **kwargs))
        return agent

class EconomicAgent(models.Model):
    """
    a party that has rights to an economicResource
    """
       
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    group = generic.GenericForeignKey("content_type", "object_id")
    agent_name = models.CharField(max_length=200)

    tags = TagField()

    objects = EconomicAgentManager()

    def __unicode__(self):
        return self.name()

    def name(self):
        if self.agent_name:
            return self.agent_name
        else:
            if self.group:
                return self.group.name
            else:
                return " ".join[("independent agent:", str(self.pk))]
            
        
    # todo: there may be no economic_agent_detail
    # or it may be the url of the group
    # or it may be a page featuring the group and its associated EconomicEvents
    # (but those shd be shown on the group's own detail page, like its other content objects)
    def get_absolute_url(self, group=None):
        kwargs = {"id": self.pk}
        if not group:
            group = self.group
        if group:
            return group.content_bridge.reverse("economic_agent_detail", group, kwargs)
        return reverse("economic_agent_detail", kwargs=kwargs)


class EconomicEvent(models.Model):
    """
    a change in an economicResource
    """
       
    resource = models.ForeignKey(EconomicResource, related_name = "economic_events")
    from_agent = models.ForeignKey(EconomicAgent, related_name = "give_events")
    to_agent = models.ForeignKey(EconomicAgent, related_name = "take_events")
    description = models.CharField(max_length=200)
    created = models.DateTimeField(_('created'), default=datetime.now)
    modified = models.DateTimeField(_('modified'), default=datetime.now)

    tags = TagField()


    def __unicode__(self):
        return " ".join([
            self.from_agent.name(),
            "gave", self.resource.name, 
            "to", self.to_agent.name(),
            "on", self.created.strftime('%Y-%m-%d'),
        ])
        #return self.description

    def save(self, force_insert=False, force_update=False):
        
        self.modified = datetime.now()
        
        super(EconomicEvent, self).save(force_insert, force_update)

    def get_absolute_url(self, group=None):
        kwargs = {"id": self.pk}
        if not group:
            group = self.group
        if group:
            return group.content_bridge.reverse("economic_event_detail", group, kwargs)
        return reverse("economic_event_detail", kwargs=kwargs)

