from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from sagepaypi.conf import get_setting
from sagepaypi.forms import Complete3DSecureForm
from sagepaypi.models import Transaction


class Complete3DSecureView(FormView):
    form_class = Complete3DSecureForm
    transaction = None

    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    @method_decorator(require_POST)
    @method_decorator(sensitive_post_parameters())
    def dispatch(self, *args, **kwargs):
        self.transaction = Transaction.objects.get_for_token(kwargs['tidb64'], kwargs['token'])

        if not self.transaction:
            raise Http404()

        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'transaction': self.transaction
        })
        return kwargs

    def form_valid(self, form):
        self.transaction = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        raise Http404()

    def get_success_url(self):
        tidb64, token = self.transaction.get_tokens()
        kwargs = {'tidb64': tidb64, 'token': token}
        return reverse(get_setting('POST_3D_SECURE_REDIRECT_URL'), kwargs=kwargs)
