from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from django.conf import settings

#if "notification" in settings.INSTALLED_APPS:
#    from notification import models as notification
#else:
#    notification = None

notification = None

from projects.models import Project, ProjectMember
from projects.forms import ProjectForm, ProjectUpdateForm, AddUserForm

TOPIC_COUNT_SQL = """
SELECT COUNT(*)
FROM topics_topic
WHERE
    topics_topic.object_id = projects_project.id AND
    topics_topic.content_type_id = %s
"""
MEMBER_COUNT_SQL = """
SELECT COUNT(*)
FROM projects_projectmember
WHERE projects_projectmember.project_id = projects_project.id
"""

@login_required
def create(request, form_class=ProjectForm, template_name="projects/create.html", parent_slug=None, bridge=None):

    parent_type = ""
    body_class = "projects"
    if bridge:
        try:
            parent = bridge.get_group(parent_slug)
            parent_type = parent._meta.verbose_name.title()
            body_class = parent._meta.verbose_name
        except ObjectDoesNotExist:
            raise Http404
    else:
        parent = None
    #import pdb; pdb.set_trace()
    if parent:
        parent_base = bridge.group_base_template()
    else:
        parent_base = None
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        if parent:
            is_member = parent.user_is_member(request.user)
        else:
            is_member = True

    project_form = form_class(request.user, parent, request.POST or None)
    
    if project_form.is_valid():
        #import pdb; pdb.set_trace()
        project = project_form.save(commit=False)
        project.creator = request.user
        project.group = parent
        project.save()
        project_member = ProjectMember(project=project, user=request.user)
        project.members.add(project_member)
        project_member.save()
        if notification:
            if parent:
                notify_list = parent.member_queryset()
            else:
                notify_list = User.objects.all() # @@@
            notify_list = notify_list.exclude(id__exact=request.user.id)
            notification.send(notify_list, "projects_new_project",
                {"project": project}, queue=True)
        if parent:
            redirect_to = bridge.reverse("project_list", parent, "projects")
        else:
            redirect_to = reverse("project_list")
        return HttpResponseRedirect(redirect_to)
        #return HttpResponseRedirect(project.get_absolute_url())

    
    return render_to_response(template_name, {
        "project_form": project_form,
        "parent": parent,
        "parent_type": parent_type,
        "is_member": is_member,
        "parent_base": parent_base,
        "body_class": body_class,
    }, context_instance=RequestContext(request))


def projects(request, template_name="projects/projects.html", parent_slug=None, bridge=None):

    parent_type = ""
    body_class = "projects"
    if bridge:
        try:
            parent = bridge.get_group(parent_slug)
            parent_type = parent._meta.verbose_name.title()
            body_class = parent._meta.verbose_name
        except ObjectDoesNotExist:
            raise Http404
    else:
        parent = None
   
    if not request.user.is_authenticated():
        is_member = False
    else:
        if parent:
            is_member = parent.user_is_member(request.user)
        else:
            is_member = True
        
    if parent:
        projects = parent.content_objects(Project)
        parent_base = bridge.group_base_template()
    else:
        projects = Project.objects.filter(object_id=None)
        parent_base = None  
    
    #projects = Project.objects.all()
    
    search_terms = request.GET.get('search', '')
    if search_terms:
        projects = (projects.filter(name__icontains=search_terms) |
            projects.filter(description__icontains=search_terms))
    
    content_type = ContentType.objects.get_for_model(Project)
    
    projects = projects.extra(select=SortedDict([
        ('member_count', MEMBER_COUNT_SQL),
        ('topic_count', TOPIC_COUNT_SQL),
    ]), select_params=(content_type.id,))
    
    return render_to_response(template_name, {
        "parent": parent,
        "parent_type": parent_type,
        "is_member": is_member,
        "parent_base": parent_base,
        'projects': projects,
        'search_terms': search_terms,
        "body_class": body_class,
    }, context_instance=RequestContext(request))


def delete(request, project_slug=None, redirect_url=None):
    project = get_object_or_404(Project, slug=project_slug)
    if not redirect_url:
        redirect_url = reverse('project_list')
    
    # @@@ eventually, we'll remove restriction that project.creator can't leave project but we'll still require project.members.all().count() == 1
    if (request.user.is_authenticated() and request.method == "POST" and
            request.user == project.creator and project.members.all().count() == 1):
        project.delete()
        request.user.message_set.create(message=_("Project %(project_name)s deleted.") % {"project_name": project.name})
        # no notification required as the deleter must be the only member
    
    return HttpResponseRedirect(redirect_url)


@login_required
def your_projects(request, template_name="projects/your_projects.html", parent_slug=None, bridge=None):

    parent_type = ""
    body_class = "projects"
    if bridge:
        try:
            parent = bridge.get_group(parent_slug)
            # todo: bad code, fix both of the next statements
            parent_type = parent._meta.verbose_name.title()
            body_class = parent._meta.verbose_name
        except ObjectDoesNotExist:
            raise Http404
    else:
        parent = None

    if parent:
        projects = parent.content_objects(Project)
        parent_base = bridge.group_base_template()
    else:
        projects = Project.objects.filter(object_id=None)
        parent_base = None  

    projects = projects.filter(member_users=request.user).order_by("name")

    content_type = ContentType.objects.get_for_model(Project)

    projects = projects.extra(select=SortedDict([
        ('member_count', MEMBER_COUNT_SQL),
        ('topic_count', TOPIC_COUNT_SQL),
    ]), select_params=(content_type.id,))

    return render_to_response(template_name, {
        "projects": projects,
        "parent": parent,
        "parent_type": parent_type,
        "parent_base": parent_base,
        "body_class": body_class,
    }, context_instance=RequestContext(request))


def project(request, project_slug=None, form_class=ProjectUpdateForm, adduser_form_class=AddUserForm,
        template_name="projects/project.html", parent_slug=None, bridge=None):
    project = get_object_or_404(Project, slug=project_slug)

    parent_type = ""
    body_class = "projects"
    if bridge:
        try:
            parent = bridge.get_group(parent_slug)
            parent_type = parent._meta.verbose_name.title()
            body_class = parent._meta.verbose_name
        except ObjectDoesNotExist:
            raise Http404
    else:
        parent = None

    if parent:
        parent_base = bridge.group_base_template()
    else:
        parent_base = None
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        is_member = project.user_is_member(request.user)
    
    action = request.POST.get("action")
    if request.user == project.creator and action == "update":
        project_form = form_class(request.user, parent, request.POST, instance=project)
        if project_form.is_valid():
            project = project_form.save()
    else:
        project_form = form_class(request.user, parent, instance=project)
    if request.user == project.creator and action == "add":
        adduser_form = adduser_form_class(request.POST, project=project)
        if adduser_form.is_valid():
            adduser_form.save(request.user)
            adduser_form = adduser_form_class(project=project) # clear form
    else:
        adduser_form = adduser_form_class(project=project)
    
    return render_to_response(template_name, {
        "project_form": project_form,
        "adduser_form": adduser_form,
        "project": project,
        "parent": parent, 
        "is_member": is_member,
        "parent_type": parent_type,
        "parent_base": parent_base,
        "body_class": body_class,
    }, context_instance=RequestContext(request))
