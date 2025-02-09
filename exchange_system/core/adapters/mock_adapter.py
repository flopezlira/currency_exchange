import random
from datetime import datetime, date
import logging
from icecream import ic
from .base_adapter import BaseAdapter

logger = logging.getLogger("core")

class MockAdapter(BaseAdapter):
    """
    Simulated currency exchange provider without making real HTTP requests.
    This class extends the BaseAdapter and provides mock exchange rates.
    """

    FAKE_API_KEY = "mock-api-key"  # A constant representing a fake API key.

    def __init__(self, provider):
        """
        Initializes the MockAdapter with a fake API key.

        Args:
            provider: The provider instance to be used with this adapter.
        """
        super().__init__(provider)
        self.api_key = self.FAKE_API_KEY

    def get_exchange_rates(self, base_currency="EUR", date=None, provider=None):
        """
        Simulates exchange rates with random fluctuations.

        Args:
            base_currency (str): The base currency for exchange rates. Defaults to "EUR".
            date (str): The date for which to simulate exchange rates. Defaults to None, which uses today's date.
            provider: The provider instance to be used. Must not be None.

        Returns:
            dict: A dictionary containing the timestamp, date, base currency, and simulated exchange rates.
        """
        ic(f"Provider: {provider}")  # Log the provider for debugging.
        ic(f"Date: {date}")  # Log the date for debugging.
        
        if provider is None:
            raise ValueError("❌ MockAdapter requires a valid provider instance!")

        today = datetime.today().strftime("%Y-%m-%d")  # Get today's date in YYYY-MM-DD format.
        simulated_date = date if date else today  # Use the provided date or default to today.
        
        # Reference rates with random fluctuations for simulation.
        reference_rates = {
            "USD": random.uniform(1.08, 1.15),
            "CHF": random.uniform(0.94, 1.00),
            "GBP": random.uniform(0.80, 0.88),
        }

        # Round the simulated rates to 6 decimal places.
        rates = {symbol: round(reference_rates[symbol], 6) for symbol in self.SUPPORTED_CURRENCIES}

        logger.info(f"MockAdapter returning simulated rates for {simulated_date}: {rates}")

        return {
            "timestamp": int(datetime.now().timestamp()),  # Current timestamp.
            "date": simulated_date,  # The date for the rates.
            "base": "EUR",  # Base currency.
            "rates": rates,  # Simulated exchange rates.
        }
