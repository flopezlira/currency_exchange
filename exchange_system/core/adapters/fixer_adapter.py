import abc
import logging
import random
from datetime import date, datetime, timedelta
from icecream import ic
import requests
from .base_adapter import BaseAdapter

logger = logging.getLogger("core")


class FixerAdapter(BaseAdapter):
    """
    Adapter for retrieving exchange rates from Fixer.io.
    """

    def get_exchange_rates(self, base_currency="EUR", date=None, provider=None):
        """
        Fetches exchange rates from Fixer.io for a single date.

        Args:
            base_currency (str): The base currency for exchange rates. Default is "EUR".
            date (str): The date for which to fetch exchange rates in 'YYYY-MM-DD' format. 
                        If None, fetches the latest rates.
            provider (object): An instance of a provider with a method get_api_key() 
                               that returns the API key for Fixer.io.

        Returns:
            dict: A dictionary containing the timestamp, date, base currency, and rates.
        
        Raises:
            ValueError: If the provider is None or does not have a valid API key.
        """
        ic(f"Provider: {provider}")
        ic(f"Date: {date}")
        
        # Check if provider and API key are valid
        if provider is None or provider.get_api_key() is None:
            raise ValueError("❌ FixerAdapter requires a valid provider instance with an API key!")

        api_key = provider.get_api_key()
        today = datetime.today().strftime("%Y-%m-%d")
        
        # Determine if fetching latest or historical rates
        if date is None or date == today:
            ic(self.current_rates_url)
            url = self.current_rates_url  # ✅ Fixer.io requires 'latest' for today's rates
            ic(f"URL: {url}")
            params = {
                "access_key": api_key,
                "base": "EUR",  # Fixer.io free tier requires EUR as base currency
            }
            data = self.make_request(url, params)
            return {
                "timestamp": data.get("timestamp"),
                "date": data.get("date"),
                "base": "EUR",
                "rates": self.extract_rates(data),
            }
        else:
            url = self.historical_rates_url.format(date=date)  # ✅ Correct historical format
            ic(f"URL: {url}")
            params = {
                "access_key": api_key,
                "base": "EUR",  # Fixer.io free tier requires EUR as base currency
            }
            data = self.make_request(url, params)
            return {
                "timestamp": data.get("timestamp"),
                "date": data.get("date"),
                "base": "EUR",
                "rates": self.extract_rates(data),
            }