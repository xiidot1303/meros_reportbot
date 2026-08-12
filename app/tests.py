from datetime import datetime
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from app.models import Order
from app.services import notification_service
from app.services.soliq_service import authenticate, soliqRequest


class NotificationServiceTests(SimpleTestCase):
    @patch("app.services.notification_service.send_newsletter_with_document")
    @patch("app.services.notification_service.get_order_report_bytes")
    def test_send_order_report_for_archived_order(self, mock_get_bytes, mock_send_document):
        order = Order(
            status="A",
            deal_id="12345",
            deal_datetime=datetime(2024, 1, 1, 12, 0, 0),
            manager="Manager",
            tin="123456789",
            total_amount=1000,
        )
        bot_user = Mock(lang=0, user_id=42)
        mock_get_bytes.return_value = b"report-data"

        notification_service.send_order_report_to_user(order, bot_user)

        mock_get_bytes.assert_called_once_with(order)
        mock_send_document.assert_called_once()
        self.assertEqual(mock_send_document.call_args.args[0], 42)
        self.assertEqual(mock_send_document.call_args.args[1], b"report-data")
        self.assertIn("report", mock_send_document.call_args.kwargs["document_name"].lower())


class SoliqServiceTests(SimpleTestCase):
    @patch("app.services.soliq_service.requests.post")
    def test_authenticate_returns_access_token_and_platform_id(self, mock_post):
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "data": {
                "client_platform": {"id": "platform-123"},
                "token": {"access_token": "token-456"},
            }
        }

        result = authenticate("user", "pass")

        self.assertEqual(result, {"accessToken": "token-456", "platformId": "platform-123"})
        mock_post.assert_called_once()

    @patch("app.services.soliq_service.authenticate")
    @patch("app.services.soliq_service.get_valid_token")
    @patch("app.services.soliq_service.requests.request")
    def test_soliq_request_refreshes_token_on_auth_failure(self, mock_request, mock_get_valid_token, mock_authenticate):
        mock_get_valid_token.return_value = {"accessToken": "expired-token", "platformId": "old-platform"}
        mock_authenticate.return_value = {"accessToken": "fresh-token", "platformId": "new-platform"}

        first_response = Mock(status_code=401, text="Unauthorized")
        first_response.json.return_value = {"message": "Unauthorized"}
        second_response = Mock(status_code=200, text="OK")
        second_response.json.return_value = {"status": "OK"}
        mock_request.side_effect = [first_response, second_response]

        result = soliqRequest("/api/v3/lists", {"method": "get", "params": {"path": "sent"}})

        self.assertEqual(result, {"status": "OK"})
        self.assertEqual(mock_request.call_count, 2)
        self.assertEqual(mock_authenticate.call_count, 1)
        self.assertIn("Bearer fresh-token", mock_request.call_args_list[1].kwargs["headers"]["authorization"])
