import logging
import os
from datetime import date

import django
from django.core.management.base import BaseCommand
from django.db import transaction
from icecream import ic

from core.state_boxes import HistoricalExchangeRateState
from core.management.tasks import update_daily_rates

# Set up a logger for the core module
logger = logging.getLogger("core")

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
# Initialize Django
django.setup()

class Command(BaseCommand):
    """
    Django management command to update daily exchange rates.
    """

    help = 'Updates daily exchange rates'

    def handle(self, *args, **kwargs):
        """
        The main entry point for the command. It logs the start of the update process,
        calls the update_daily_rates function, and logs the success or failure of the operation.
        """
        ic(f"Starting daily exchange rate update...")  # Debugging output
        logger.info("Starting daily exchange rate update...")  # Log the start of the update process
        try:
            # Call the function to update daily exchange rates
            update_daily_rates()
            # Log and print success message
            self.stdout.write(self.style.SUCCESS('Successfully updated daily exchange rates'))
            logger.info("Successfully updated daily exchange rates")
        except Exception as e:
            # Log and print error message if an exception occurs
            logger.error(f"Error updating daily exchange rates: {e}")
            self.stdout.write(self.style.ERROR('Failed to update daily exchange rates'))

