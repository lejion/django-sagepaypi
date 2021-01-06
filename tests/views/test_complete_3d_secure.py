import mock
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from sagepaypi.models import Transaction
from tests.mocks import auth_success_response, outcome_live_response

from tests.test_case import AppTestCase


class TestView(AppTestCase):
    fixtures = ['tests/fixtures/test']

    def setUp(self):
        self.transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        self.transaction.transaction_id = 'random-id'
        self.transaction.save()

        self.tidb64, self.token = self.transaction.get_tokens()
        self.url = reverse(
            'sagepaypi:complete_3d_secure',
            kwargs={'tidb64': self.tidb64, 'token': self.token}
        )

    def test_get_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_post_with_invalid_tokens_raises_404(self):
        url = reverse('sagepaypi:complete_3d_secure', kwargs={'tidb64': 'invalid', 'token': self.token})
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, 404)

        url = reverse('sagepaypi:complete_3d_secure', kwargs={'tidb64': self.tidb64, 'token': 'invalid'})
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, 404)

    def test_post_with_invalid_data_raises_404(self):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, 404)

    @override_settings(SAGEPAYPI_POST_3D_SECURE_REDIRECT_URL='secure_post_redirect')
    @mock.patch('sagepaypi.gateway.default_gateway')
    def test_post_with_valid_data(self, mock_gateway):
        mock_gateway.get_3d_secure_status.return_value = auth_success_response()
        mock_gateway.get_transaction_outcome.return_value = outcome_live_response()

        response = self.client.post(self.url, data={'PaRes': 'random-pares'})

        self.transaction.refresh_from_db()

        tidb64, token = self.transaction.get_tokens()

        expected_url = reverse(
            settings.SAGEPAYPI_POST_3D_SECURE_REDIRECT_URL,
            kwargs={'tidb64': tidb64, 'token': token})

        self.assertRedirects(response, expected_url)
