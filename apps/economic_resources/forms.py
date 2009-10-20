from datetime import datetime
from sys import stderr

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_app
from django.utils.translation import ugettext

from django.contrib.auth.models import User

from economic_resources.models import EconomicResource
from tasks.widgets import ReadOnlyWidget

from tagging_utils.widgets import TagAutoCompleteInput
from tagging.forms import TagField

class EconomicResourceForm(forms.ModelForm):
    def __init__(self, user, group, *args, **kwargs):
        self.user = user
        self.group = group
        
        super(EconomicResourceForm, self).__init__(*args, **kwargs)
            
    def save(self, commit=True):
        
        return super(EconomicResourceForm, self).save(commit)
    
    tags = TagField(required=False, widget=TagAutoCompleteInput(app_label='economic_resources', model='economicresource'))
    
    class Meta:
        model = EconomicResource
        fields = ('name', 'tags')
    
    def clean(self):
        self.check_group_membership()
        return self.cleaned_data
    
    def check_group_membership(self):
        group = self.group
        if group and not self.group.user_is_member(self.user):
            raise forms.ValidationError("You must be a member to create economic_resources")


class EditEconomicResourceForm(forms.ModelForm):
    """
    a form for editing economic_resource
    """
    
    
    def __init__(self, user, group, *args, **kwargs):
        self.user = user
        self.group = group
        
        super(EditEconomicResourceForm, self).__init__(*args, **kwargs)
      
    
    def save(self, commit=False):
        
        return super(EditEconomicResourceForm, self).save(True)

    tags = TagField(required=False, widget=TagAutoCompleteInput(app_label='economic_resources', model='economicresource'))
    
    class Meta(EconomicResourceForm.Meta):
        fields = ('name', 'tags')
    

