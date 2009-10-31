from datetime import datetime
from sys import stderr

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_app
from django.utils.translation import ugettext

from django.contrib.auth.models import User

from economic_events.models import EconomicAgent, EconomicEvent
from economic_resources.models import EconomicResource
from tasks.widgets import ReadOnlyWidget

from tagging_utils.widgets import TagAutoCompleteInput
from tagging.forms import TagField

class GiveEconomicEventForm(forms.ModelForm):
    def __init__(self, user, group, *args, **kwargs):
        self.user = user
        self.group = group
        agent = EconomicAgent.objects.agent_for_object(group)
        
        # todo: counterparties might not have agents, 
        # so to_agent.choices might be incorrectly empty
        # Shd agents be pre-registered?
        # also, shd to_agent eliminate from_agent?  Or not?
        super(GiveEconomicEventForm, self).__init__(*args, **kwargs)
        self.fields['from_agent'].choices = [(agent.id, agent)]
        self.fields['resource'].choices = [('', '----------')] + [(resource.id, resource.name) for resource in group.content_objects(EconomicResource)]

            
    def save(self, commit=True):
        
        return super(GiveEconomicEventForm, self).save(commit)
    
    tags = TagField(required=False, widget=TagAutoCompleteInput(app_label='economic_events', model='economicevent'))
    
    class Meta:
        model = EconomicEvent
        fields = ('resource', 'from_agent', 'to_agent', 'description', 'tags')
    
    def clean(self):
        self.check_group_membership()
        return self.cleaned_data
    
    def check_group_membership(self):
        group = self.group
        if group and not self.group.user_is_member(self.user):
            raise forms.ValidationError("You must be a member to create economic_events")


class EditEconomicEventForm(forms.ModelForm):
    """
    a form for editing economic_event
    """
     
    def __init__(self, user, group, *args, **kwargs):
        self.user = user
        self.group = group
        
        super(EditEconomicEventForm, self).__init__(*args, **kwargs)
      
    
    def save(self, commit=False):
        
        return super(EditEconomicEventForm, self).save(True)

    tags = TagField(required=False, widget=TagAutoCompleteInput(app_label='economic_events', model='economicevent'))
    
    class Meta:
        model = EconomicEvent
        fields = ('resource', 'from_agent', 'to_agent', 'description', 'tags')
    
class TakeEconomicEventForm(forms.ModelForm):
    def __init__(self, user, group, *args, **kwargs):
        self.user = user
        self.group = group
        
        super(TakeEconomicEventForm, self).__init__(*args, **kwargs)
        self.fields['to_agent'].choices = [(group.id, group)]

            
    def save(self, commit=True):
        
        return super(TakeEconomicEventForm, self).save(commit)
    
    tags = TagField(required=False, widget=TagAutoCompleteInput(app_label='economic_events', model='economicevent'))
    
    class Meta:
        model = EconomicEvent
        fields = ('resource', 'from_agent', 'to_agent', 'description', 'tags')
    
    def clean(self):
        self.check_group_membership()
        return self.cleaned_data
    
    def check_group_membership(self):
        group = self.group
        if group and not self.group.user_is_member(self.user):
            raise forms.ValidationError("You must be a member to create economic_events")
