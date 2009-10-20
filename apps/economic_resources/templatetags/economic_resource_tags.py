from django import template

from django.contrib.contenttypes.models import ContentType

from django.core.urlresolvers import reverse
from django.conf import settings

from tagging.models import Tag, TaggedItem
from tagging.utils import parse_tag_input

from economic_resources.models import EconomicResource

import re

register = template.Library()
economic_resource_contenttype = ContentType.objects.get(app_label='economic_resources', model='economicresource')

@register.inclusion_tag("economic_resources/economic_resource_item.html", takes_context=True)
def show_economic_resource(context, economic_resource):
    
    return {
        "economic_resource": economic_resource,
        "MEDIA_URL": settings.MEDIA_URL,
        "STATIC_URL": settings.STATIC_URL,
        "group": context["group"],
    }


@register.inclusion_tag("economic_resources/tag_list.html")
def economic_resource_tags(obj, group=None):
    taglist = parse_tag_input(obj.tags)
    return {
        "tags": taglist,
        "group": group,
    }

class EconomicResourcesForTagNode(template.Node):
    def __init__(self, tag, var_name, selection):
        self.tag = tag
        self.var_name = var_name
        self.selection = selection

    def render(self, context):
        try:
            tag = template.Variable(self.tag).resolve(context)
        except:
            tag = self.tag
        
        try:
            selection = template.Variable(self.selection).resolve(context)
        except:
            selection = EconomicResource.objects.all()
        
        try:
            economic_resources = selection.filter(id__in=[i[0] for i in TaggedItem.objects.filter(tag__name=str(tag),content_type=economic_resource_contenttype).values_list('object_id')])
        except:
            return ''
        
        context[self.var_name] = economic_resources
        return ''

@register.tag(name='economic_resources_for_tag')
def economic_resources_for_tag(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]

    m = re.search(r'(\w+) as (\w+) in (\w+)', arg)
    if not m:
        m = re.search(r'(\w+) as (\w+)', arg)
        if not m:
            raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name

    tag = m.groups()[0]
    var_name = m.groups()[1]
    try:
        selection = m.groups()[2]
    except IndexError:
        selection = None

    return EconomicResourcesForTagNode(tag, var_name, selection)

@register.filter
def simple_linebreak(text):
    # TODO: replace with better tooltip feature or detail page
    return '<br />'.join(text.splitlines())
    
