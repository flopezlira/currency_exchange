import logging
import os

from cryptography.fernet import Fernet
from django.core.exceptions import ValidationError
from django.db import models

# Set up logging for the core module
logger = logging.getLogger("core")

# Generate a secret key if not already set (must be stored securely)
SECRET_KEY_PATH = os.path.join(os.path.dirname(__file__), "secret.key")
if os.path.exists(SECRET_KEY_PATH):
    with open(SECRET_KEY_PATH, "rb") as key_file:
        SECRET_KEY = key_file.read()
else:
    SECRET_KEY = Fernet.generate_key()
    with open(SECRET_KEY_PATH, "wb") as key_file:
        key_file.write(SECRET_KEY)

# Initialize the cipher suite with the secret key
cipher_suite = Fernet(SECRET_KEY)


class Currency(models.Model):
    """
    Represents one of the supported currencies: EUR, CHF, USD, GBP.
    """

    code = models.CharField(
        max_length=3,
        unique=True,
        choices=[
            ("EUR", "Euro"),
            ("CHF", "Swiss Franc"),
            ("USD", "US Dollar"),
            ("GBP", "British Pound"),
        ],
    )
    name = models.CharField(max_length=20)  # Currency name (e.g., Euro, Dollar)
    symbol = models.CharField(max_length=10)  # Currency symbol (e.g., €, $)

    def __str__(self) -> str:
        """
        Return a string representation of the currency.
        """
        return f"{self.code} ({self.name})"


class ExchangeRate(models.Model):
    """
    Stores exchange rates with EUR as the base currency.
    """

    valuation_date = models.DateField(db_index=True)  # Date of exchange rate
    chf_rate = models.DecimalField(max_digits=18, decimal_places=6)  # EUR -> CHF
    usd_rate = models.DecimalField(max_digits=18, decimal_places=6)  # EUR -> USD
    gbp_rate = models.DecimalField(max_digits=18, decimal_places=6)  # EUR -> GBP

    class Meta:
        unique_together = ("valuation_date",)  # Prevent duplicate entries per date

    def __str__(self) -> str:
        """
        Return a string representation of the exchange rates for a specific date.
        """
        return f"Rates on {self.valuation_date}"


class Provider(models.Model):
    """
    Stores currency data providers like Fixer.io and mock providers.
    """

    name = models.CharField(
        max_length=100, unique=True
    )  # Provider name (e.g., Fixer.io)
    current_rates_url = models.URLField()  # URL for latest exchange rates
    historical_rates_url = models.URLField(
        default="http://example.com/historical"
    )  # Default URL for historical rates
    adapter_path = models.CharField(max_length=255)  # Path to the Python adapter
    priority = models.IntegerField(unique=True)  # Lower values = higher priority
    active = models.BooleanField(
        default=True
    )  # Whether the provider is currently in use
    last_failure = models.DateTimeField(
        null=True, blank=True
    )  # Last recorded failure timestamp
    _api_key = models.BinaryField(
        default=b"", editable=False
    )  # Encrypted API key storage

    def __str__(self):
        """
        Return the name of the provider.
        """
        return self.name

    def set_api_key(self, raw_api_key) -> None:
        """
        Encrypt and store the API key.

        Args:
            raw_api_key (str): The raw API key to be encrypted and stored.
        """
        encrypted_key = cipher_suite.encrypt(raw_api_key.encode())
        self._api_key = encrypted_key
        self.save()

    def get_api_key(self) -> str:
        """
        Decrypt and return the provider's API key.

        Returns:
            str: The decrypted API key, or None if decryption fails.
        """
        if not self._api_key:
            return None

        try:
            decrypted_key = cipher_suite.decrypt(self._api_key).decode()
            return decrypted_key
        except Exception as e:
            logger.error(f"❌ Error decrypting API key: {e}")
            return None

    def clean(self) -> None:
        """
        Ensure priority is always a positive integer.

        Raises:
            ValidationError: If the priority is not a positive integer.
        """
        if self.priority < 1:
            raise ValidationError("Priority must be a positive integer.")
