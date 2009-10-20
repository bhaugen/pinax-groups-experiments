from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse

from tagging.fields import TagField
from tagging.models import Tag

class EconomicResourceManager(models.Manager):

    def _generate_object_kwarg_dict(self, content_object, **kwargs):
        """
        Generates the most comment keyword arguments for a given ``content_object``.
        """
        kwargs['content_type'] = ContentType.objects.get_for_model(content_object)
        kwargs['object_id'] = getattr(content_object, 'pk', getattr(content_object, 'id'))
        return kwargs

	# todo: maybe delete, already done by group.content_objects
    def resources_for_object(self, content_object, **kwargs):
        """
        Prepopulates a QuerySet with all EconomicResources related to the given ``content_object``.
        """
        return self.filter(**self._generate_object_kwarg_dict(content_object, **kwargs))


class EconomicResource(models.Model):
    """
    something of value.
    """
       
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    group = generic.GenericForeignKey("content_type", "object_id")
    name = models.CharField(max_length=200)

    tags = TagField()

    objects = EconomicResourceManager()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self, group=None):
        kwargs = {"id": self.pk}
        if not group:
            group = self.group
        if group:
            return group.content_bridge.reverse("economic_resource_detail", group, kwargs)
        return reverse("economic_resource_detail", kwargs=kwargs)

