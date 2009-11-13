from django.core.urlresolvers import reverse
from django.contrib.auth.models import  User
from django.utils.translation import ugettext_lazy as _
from django.db import models

from groups.base import Group

class Company(Group):
    
    member_users = models.ManyToManyField(User, through="CompanyMember", verbose_name=_('members'))
    
    # private means only members can see the company
    private = models.BooleanField(_('private'), default=True)
    
    def get_absolute_url(self):
        return reverse('company_detail', kwargs={'group_slug': self.slug})
    
    def member_queryset(self):
        return self.member_users.all()
    
    def user_is_member(self, user):
        if CompanyMember.objects.filter(company=self, user=user).count() > 0: # @@@ is there a better way?
            return True
        else:
            return False
    
    def get_url_kwargs(self, variant=None):
        if variant:
            return {'parent_slug': self.slug}
        else:
            return {'group_slug': self.slug}

    def group_base_template(self, template_name="content_base.html"):
        return "%s/%s" % ("company", template_name)


class CompanyMember(models.Model):
    company = models.ForeignKey(Company, related_name="members", verbose_name=_('company'))
    user = models.ForeignKey(User, related_name="companies", verbose_name=_('user'))

