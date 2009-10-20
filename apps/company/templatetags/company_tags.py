from django import template
from company.forms import CompanyForm

register = template.Library()

@register.inclusion_tag("company/company_item.html", takes_context=True)
def show_company(context, company):
    return {'company': company, 'request': context['request']}


