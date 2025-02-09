import abc
import logging
import requests

# Initialize a logger for the core module
logger = logging.getLogger("core")

class BaseAdapter(abc.ABC):
    """
    Abstract base class for currency exchange rate providers.
    Ensures all providers follow a unified structure.
    """

    # Currencies that the adapter supports
    SUPPORTED_CURRENCIES = ["CHF", "USD", "GBP"]

    def __init__(self, provider):
        """
        Initializes the adapter with provider details.

        Args:
            provider: An object that provides API key and URLs for current and historical rates.
        """
        self.provider = provider
        self.api_key = provider.get_api_key()  # Retrieve API key from the provider
        self.current_rates_url = provider.current_rates_url  # URL for fetching current rates
        self.historical_rates_url = provider.historical_rates_url  # URL for fetching historical rates

    @abc.abstractmethod
    def get_exchange_rates(self, base_currency, date=None, provider=None) -> list[dict]:
        """
        Abstract method that must be implemented by each adapter to fetch exchange rates.

        Args:
            base_currency: The currency to base the exchange rates on.
            date: Optional; the date for which to fetch historical rates.
            provider: Optional; the provider to use for fetching rates.

        Returns:
            A list of dictionaries containing exchange rate data.
        """
        pass

    def make_request(self, url, params):
        """
        Performs an HTTP request and handles errors.

        Args:
            url: The URL to send the request to.
            params: A dictionary of parameters to include in the request.

        Returns:
            The JSON response from the API.

        Raises:
            ValueError: If there is an error with the API request or response.
        """
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # Raise an error for HTTP error responses
            data = response.json()

            # Check for API-specific error messages
            if "success" in data and not data["success"]:
                raise ValueError(f"API error: {data.get('error', {}).get('info', 'Unknown error')}")

            return data
        except requests.RequestException as e:
            raise ValueError(f"Error connecting to API: {e}")

    def extract_rates(self, data, date=None):
        """
        Extracts only supported currencies from the API response.

        Args:
            data: The JSON data returned from the API.
            date: Optional; the date for which to extract rates.

        Returns:
            A dictionary of exchange rates for supported currencies.
        """
        if date:
            extracted_rates = data["data"].get(date, {})
        else:
            extracted_rates = data.get("rates", data.get("data", {}))

        # Filter and return rates for supported currencies
        return {symbol: extracted_rates.get(symbol) for symbol in self.SUPPORTED_CURRENCIES}
