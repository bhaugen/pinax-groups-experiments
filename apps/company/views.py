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

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

from company.models import Company, CompanyMember
from company.forms import CompanyForm, CompanyUpdateForm, AddUserForm

TOPIC_COUNT_SQL = """
SELECT COUNT(*)
FROM topics_topic
WHERE
    topics_topic.object_id = company_company.id AND
    topics_topic.content_type_id = %s
"""
MEMBER_COUNT_SQL = """
SELECT COUNT(*)
FROM company_companymember
WHERE company_companymember.company_id = company_company.id
"""

@login_required
def create(request, form_class=CompanyForm, template_name="company/create.html"):
    company_form = form_class(request.POST or None)
    
    if company_form.is_valid():
        company = company_form.save(commit=False)
        company.creator = request.user
        company.save()
        company_member = CompanyMember(company=company, user=request.user)
        company.members.add(company_member)
        company_member.save()
        if notification:
            # @@@ might be worth having a shortcut for sending to all users
            notification.send(User.objects.all(), "company_new_company",
                {"company": company}, queue=True)
        return HttpResponseRedirect(company.get_absolute_url())
    
    return render_to_response(template_name, {
        "company_form": company_form,
    }, context_instance=RequestContext(request))


def companies(request, template_name="company/companies.html"):
    
    companies = Company.objects.all()
    
    search_terms = request.GET.get('search', '')
    if search_terms:
        companies = (companies.filter(name__icontains=search_terms) |
            companies.filter(description__icontains=search_terms))
    
    content_type = ContentType.objects.get_for_model(Company)
    
    companies = companies.extra(select=SortedDict([
        ('member_count', MEMBER_COUNT_SQL),
        ('topic_count', TOPIC_COUNT_SQL),
    ]), select_params=(content_type.id,))
    
    return render_to_response(template_name, {
        'companies': companies,
        'search_terms': search_terms,
    }, context_instance=RequestContext(request))


def delete(request, group_slug=None, redirect_url=None):
    company = get_object_or_404(Company, slug=group_slug)
    if not redirect_url:
        redirect_url = reverse('company_list')
    
    # @@@ eventually, we'll remove restriction that company.creator can't leave company but we'll still require company.members.all().count() == 1
    if (request.user.is_authenticated() and request.method == "POST" and
            request.user == company.creator and company.members.all().count() == 1):
        company.delete()
        request.user.message_set.create(message=_("Company %(company_name)s deleted.") % {"company_name": company.name})
        # no notification required as the deleter must be the only member
    
    return HttpResponseRedirect(redirect_url)


@login_required
def your_companies(request, template_name="company/your_companies.html"):

    companies = Company.objects.filter(member_users=request.user).order_by("name")

    content_type = ContentType.objects.get_for_model(Company)

    companies = companies.extra(select=SortedDict([
        ('member_count', MEMBER_COUNT_SQL),
        ('topic_count', TOPIC_COUNT_SQL),
    ]), select_params=(content_type.id,))

    return render_to_response(template_name, {
        "companies": companies,
    }, context_instance=RequestContext(request))


def company(request, group_slug=None, form_class=CompanyUpdateForm, adduser_form_class=AddUserForm,
        template_name="company/company.html"):
    company = get_object_or_404(Company, slug=group_slug)
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        is_member = company.user_is_member(request.user)
    
    action = request.POST.get("action")
    if request.user == company.creator and action == "update":
        company_form = form_class(request.POST, instance=company)
        if company_form.is_valid():
            company = company_form.save()
    else:
        company_form = form_class(instance=company)
    if request.user == company.creator and action == "add":
        adduser_form = adduser_form_class(request.POST, company=company)
        if adduser_form.is_valid():
            adduser_form.save(request.user)
            adduser_form = adduser_form_class(company=company) # clear form
    else:
        adduser_form = adduser_form_class(company=company)
    
    return render_to_response(template_name, {
        "company_form": company_form,
        "adduser_form": adduser_form,
        "company": company,
        "group": company, # @@@ this should be the only context var for the company
        "is_member": is_member,
    }, context_instance=RequestContext(request))
