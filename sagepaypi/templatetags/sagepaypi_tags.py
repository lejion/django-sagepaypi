from django.template import Library

register = Library()


@register.inclusion_tag('sagepaypi/tags/3d_secure_redirect.html', takes_context=True)
def sagepay_secure_redirect_form(context, transaction, **kwargs):
    tidb64, token = transaction.get_tokens()
    request = context['request']
    host = request.META.get('HTTP_HOST')
    protocol = request.is_secure() and "https" or "http"
    return {
        'domain': host,
        'protocol': protocol,
        'acsurl': transaction.acs_url,
        'pareq': transaction.pareq,
        'tidb64': tidb64,
        'token': token,
        'transaction_id': transaction.transaction_id
    }
