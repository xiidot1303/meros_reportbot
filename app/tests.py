from datetime import datetime
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from app.models import Order
from app.services import notification_service


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
