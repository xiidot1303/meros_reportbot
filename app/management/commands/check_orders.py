from django.core.management.base import BaseCommand
from app.scheduled_job.smartup_job import check_orders
import warnings
from telegram.warnings import PTBUserWarning

warnings.filterwarnings(
    "ignore",
    message=r"If 'per_message=False'.*",
    category=PTBUserWarning,
)

class Command(BaseCommand):
    help = 'Update orders list from SmartUp and handle changes'

    def handle(self, *args, **kwargs):
        check_orders()