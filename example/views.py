from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DetailView

from formtools.wizard.views import SessionWizardView
from sagepaypi.conf import get_setting
from sagepaypi.forms import CardIdentifierForm
from sagepaypi.models import Transaction

from example.forms import TransactionForm


class TransactionCreateView(SessionWizardView):
    form_list = [
        ('transaction', TransactionForm),
        ('card', CardIdentifierForm),
    ]
    initial_dict = {
        'transaction': {
            'amount': 100,
            'currency': 'GBP',
            'description': 'Payment for goods'
        }
    }
    templates = {
        'transaction': 'example/forms/transaction.html',
        'card': 'example/forms/card.html',
    }

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, form_list, form_dict, **kwargs):
        transaction = form_dict['transaction'].save(commit=False)

        card_identifier = form_dict['card'].save()

        # for new cards payment type is Payment
        transaction.type = 'Payment'
        transaction.card_identifier = card_identifier
        transaction.save()

        transaction.submit_transaction()

        if transaction.requires_3d_secure:
            return render(
                self.request,
                'sagepaypi/3d_secure_redirect_form.html',
                {'transaction': transaction}
            )

        transaction.refresh_from_db()
        tidb64, token = transaction.get_tokens()

        return HttpResponseRedirect(
            reverse(
                get_setting('POST_3D_SECURE_REDIRECT_URL'),
                kwargs={'tidb64': tidb64, 'token': token}
            )
        )


class TransactionStatusView(DetailView):
    template_name = 'example/transaction_status.html'
    model = Transaction

    def get_object(self):
        tidb64 = self.kwargs['tidb64']
        token = self.kwargs['token']
        return Transaction.objects.get_for_token(tidb64, token)
