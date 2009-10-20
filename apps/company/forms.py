from django import forms
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User

from company.models import Company, CompanyMember

# @@@ we should have auto slugs, even if suggested and overrideable

class CompanyForm(forms.ModelForm):
    
    slug = forms.SlugField(max_length=20,
        help_text = _("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
        error_message = _("This value must contain only letters, numbers, underscores and hyphens."))
            
    def clean_slug(self):
        if Company.objects.filter(slug__iexact=self.cleaned_data["slug"]).count() > 0:
            raise forms.ValidationError(_("A company already exists with that slug."))
        return self.cleaned_data["slug"].lower()
    
    def clean_name(self):
        if Company.objects.filter(name__iexact=self.cleaned_data["name"]).count() > 0:
            raise forms.ValidationError(_("A company already exists with that name."))
        return self.cleaned_data["name"]
    
    class Meta:
        model = Company
        fields = ('name', 'slug', 'description')


# @@@ is this the right approach, to have two forms where creation and update fields differ?

class CompanyUpdateForm(forms.ModelForm):
    
    def clean_name(self):
        if Company.objects.filter(name__iexact=self.cleaned_data["name"]).count() > 0:
            if self.cleaned_data["name"] == self.instance.name:
                pass # same instance
            else:
                raise forms.ValidationError(_("A company already exists with that name."))
        return self.cleaned_data["name"]
    
    class Meta:
        model = Company
        fields = ('name', 'description')


class AddUserForm(forms.Form):
    
    recipient = forms.CharField(label=_(u"User"))
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company")
        super(AddUserForm, self).__init__(*args, **kwargs)
    
    def clean_recipient(self):
        try:
            user = User.objects.get(username__exact=self.cleaned_data['recipient'])
        except User.DoesNotExist:
            raise forms.ValidationError(_("There is no user with this username."))
        
        if CompanyMember.objects.filter(company=self.company, user=user).count() > 0:
            raise forms.ValidationError(_("User is already a member of this company."))
        
        return self.cleaned_data['recipient']
    
    def save(self, user):
        new_member = User.objects.get(username__exact=self.cleaned_data['recipient'])
        company_member = CompanyMember(company=self.company, user=new_member)
        company_member.save()
        self.company.members.add(company_member)
        if notification:
            notification.send(self.company.member_users.all(), "companys_new_member", {"new_member": new_member, "company": self.company})
            notification.send([new_member], "company_added_as_member", {"adder": user, "company": self.company})
        user.message_set.create(message="added %s to company" % new_member)
