import logging
import os
from datetime import date

import django
from django.db import transaction
from icecream import ic

from core.models import ExchangeRate, Provider
from core.state_boxes import HistoricalExchangeRateState

logger = logging.getLogger("core")

def update_daily_rates() -> None:
    """
    Fetches the latest exchange rates from the highest-priority provider
    and saves them to the database if they don't already exist for today.
    
    This function checks if the exchange rates for the current date are already
    present in the database. If not, it retrieves the rates using a state box
    and stores them in the database within a transaction.
    
    Logs the process and any errors encountered.
    """
    # Ensure the Django environment is loaded
    logger.info("Starting daily exchange rate update...")
    ic(f"Starting daily exchange rate update...")  # Consider removing in production
    
    try:
        today = date.today()
        # Check if exchange rates already exist for today
        if ExchangeRate.objects.filter(valuation_date=today).exists():
            logger.info("Exchange rates for today already exist. Skipping update.")
            ic(f"Exchange rates for today already exist. Skipping update.")
            return
        
        # Retrieve exchange rates using state box
        state_box = HistoricalExchangeRateState()
        rates = state_box.fetch_historical_rates("EUR", [today, today])
        
        if not rates:
            logger.error("Failed to retrieve exchange rates for today.")
            return
        
        # Store rates in the database
        with transaction.atomic():
            for rate in rates:
                # Update or create exchange rate records for today
                ExchangeRate.objects.update_or_create(
                    valuation_date=rate["valuation_date"],
                    defaults={
                        "chf_rate": rate["rates"].get("CHF"),
                        "usd_rate": rate["rates"].get("USD"),
                        "gbp_rate": rate["rates"].get("GBP"),
                    },
                )
            
        logger.info("Exchange rates updated successfully.")
        
    except Exception as e:
        logger.error(f"Error updating daily rates: {e}")
        # Consider adding more specific exception handling or retry logic
