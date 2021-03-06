from datetime import datetime

from django.core.urlresolvers import reverse
from django.contrib.auth.models import  User
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from groups.base import Group

class Project(Group):
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    group = generic.GenericForeignKey("content_type", "object_id")

    member_users = models.ManyToManyField(User, through="ProjectMember", verbose_name=_('members'))
    
    # private means only members can see the project
    private = models.BooleanField(_('private'), default=False)

    def get_absolute_url(self, group=None):
        #kwargs = {"id": self.pk, 'group_slug': self.slug}
        if not group:
            group = self.group
        if group:
            return group.content_bridge.reverse("project_detail", group, {"id": self.pk})
        return reverse("project_detail", kwargs={'project_slug': self.slug})
    
    def get_absolute_url_old(self):
        return reverse('project_detail', kwargs={'group_slug': self.slug})
    
    def member_queryset(self):
        return self.member_users.all()
    
    def user_is_member(self, user):
        if ProjectMember.objects.filter(project=self, user=user).count() > 0: # @@@ is there a better way?
            return True
        else:
            return False
    
    def get_url_kwargs(self, variant=None):
        return {'group_slug': self.slug}


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, related_name="members", verbose_name=_('project'))
    user = models.ForeignKey(User, related_name="projects", verbose_name=_('user'))
    
    away = models.BooleanField(_('away'), default=False)
    away_message = models.CharField(_('away_message'), max_length=500)
    away_since = models.DateTimeField(_('away since'), default=datetime.now)
