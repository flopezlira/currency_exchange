import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db import models, transaction
from icecream import ic

from .adapters import load_adapter
from .models import ExchangeRate, Provider
from .pydantic_models.exchange_rates import ExchangeRateModel

logger = logging.getLogger("core")


class CurrencyConversionState:
    def __init__(self):
        """
        Initializes the CurrencyConversionState with default values.
        """
        self.state = "Ready"  # Initial state
        self.converted_amount = None
        self.exchange_rate = None
        self.error_message = None

    def process_request(self, source_currency, target_currency, amount) -> float:
        """
        Processes the conversion request between two currencies using the latest exchange rate.

        Parameters:
        - source_currency (str): The currency to convert from.
        - target_currency (str): The currency to convert to.
        - amount (float): The amount to be converted.

        Returns:
        - float: The converted amount or None if an error occurs.
        """
        logger.info(
            f"Processing conversion from {source_currency} to {target_currency} for amount {amount}."
        )
        self.state = "Processing Request"

        # Validate input parameters
        if amount <= 0:
            self.state = "Error"
            self.error_message = "Amount must be greater than zero."
            logger.error(self.error_message)
            return None

        if source_currency == target_currency:
            self.state = "Error"
            self.error_message = "Same currency conversion requested."
            logger.error(self.error_message)
            return None  # No conversion needed if currencies are the same

        try:
            # Step 1: Retrieve the latest exchange rate from the database or cache
            self.exchange_rate = self.get_exchange_rate(
                source_currency, target_currency
            )

            if not self.exchange_rate:
                # Step 2: Fetch all rates from an external provider as a fallback
                self.state = "Fetching External Data"
                self.fetch_and_store_rates()

                # Step 3: Retrieve the exchange rate again after fetching
                self.exchange_rate = self.get_exchange_rate(
                    source_currency, target_currency
                )

            if not self.exchange_rate:
                raise ValueError("Failed to retrieve exchange rate.")

            # Step 4: Perform the conversion
            # Convert amount to Decimal for greater precision
            amount_decimal = Decimal(str(amount))
            self.converted_amount = amount_decimal * self.exchange_rate
            self.state = "Completed"
            logger.info(
                f"Converted {amount} {source_currency} to {self.converted_amount:.2f} {target_currency}."
            )
            return float(self.converted_amount)  # Convert to float if necessary
        except Exception as e:
            self.state = "Error"
            self.error_message = str(e)
            logger.error(f"Error during conversion: {self.error_message}")
            return None

    def get_exchange_rate(self, source_currency, target_currency) -> float:
        """
        Retrieves the latest exchange rate between two currencies from the database or cache.

        Parameters:
        - source_currency (str): The currency to convert from.
        - target_currency (str): The currency to convert to.

        Returns:
        - Decimal: The exchange rate or None if not found.
        """
        try:
            today = date.today().strftime("%Y-%m-%d")
            cache_key = f"exchange_rate_{source_currency}_{target_currency}_{today}"
            cached_rate = cache.get(cache_key)
            if cached_rate:
                ic(
                    f"Using cached exchange rate for {source_currency} to {target_currency} on {today}."
                )
                logger.info(
                    f"Using cached exchange rate for {source_currency} to {target_currency} on {today}."
                )
                return Decimal(str(cached_rate))

            # Retrieve the latest exchange rate entry
            rate = ExchangeRate.objects.order_by("-valuation_date").first()

            if not rate:
                return None
            ic(
                f"Using latest exchange rate from database for {source_currency} to {target_currency}."
            )
            # Map rates, including EUR with a fixed rate of 1.0
            rates = {
                "EUR": Decimal("1.0"),  # Base currency
                "CHF": rate.chf_rate,
                "USD": rate.usd_rate,
                "GBP": rate.gbp_rate,
            }

            # Calculate the exchange rate between the source and target currency
            source_to_base = rates.get(source_currency)
            target_to_base = rates.get(target_currency)

            ic(f"Source currency: {source_currency}")
            ic(f"Target currency: {target_currency}")
            ic(f"Source to base: {source_to_base}!!!")
            ic(f"Target to base: {target_to_base}!!!")

            if source_to_base is None or target_to_base is None:
                raise ValueError(
                    f"Exchange rate for {source_currency} or {target_currency} not available."
                )

            exchange_rate = target_to_base / source_to_base

            # Cache for future use
            cache.set(
                cache_key, float(exchange_rate), timeout=86400
            )  # Cache for 24 hours
            return exchange_rate
        except Exception as e:
            logger.error(f"Error retrieving exchange rate: {e}")
            return None

    def fetch_and_store_rates(self) -> None:
        """
        Fetches exchange rates from the external provider and stores them in the database.
        """
        providers = Provider.objects.filter(active=True).order_by("priority")

        for provider in providers:
            try:
                logger.debug(f"Fetching exchange rates from {provider.name}.")
                adapter = load_adapter(provider)
                rates_data = adapter.get_exchange_rates(
                    base_currency="EUR", provider=provider
                )
                logger.debug(f"Rates fetched: {rates_data}")

                if rates_data and "rates" in rates_data:
                    rates = rates_data["rates"]
                    valuation_date = rates_data.get("date", date.today())

                    # Pass all required rates to the storage method
                    self.store_exchange_rates(
                        rates=rates, valuation_date=valuation_date
                    )
                    logger.info(
                        f"Exchange rates from {provider.name} stored successfully."
                    )
                    break  # Exit after successfully storing rates from the highest-priority provider
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue  # Try the next provider

        else:
            logger.error("All providers failed to fetch exchange rates.")
            raise ValueError("All providers failed to fetch exchange rates.")

    def store_exchange_rates(self, rates, valuation_date=None) -> None:
        """
        Stores the fetched exchange rates in the database and cache for future use.

        Parameters:
        - rates (dict): A dictionary containing all required exchange rates relative to EUR.
          Example:
            {
                'CHF': 0.940122,
                'USD': 1.033218,
                'GBP': 0.833213
            }
        - valuation_date (date, optional): The date of the exchange rates. Defaults to today.
        """
        try:
            valuation_date = valuation_date or date.today()

            # Validate that all required rates are present
            required_currencies = ["CHF", "USD", "GBP"]
            missing_currencies = [
                currency for currency in required_currencies if currency not in rates
            ]

            if missing_currencies:
                logger.error(f"Missing rates for: {', '.join(missing_currencies)}")
                raise ValueError(f"Missing rates for: {', '.join(missing_currencies)}")

            # Convert rates to Decimal to ensure proper storage
            chf_rate = Decimal(str(rates["CHF"]))
            usd_rate = Decimal(str(rates["USD"]))
            gbp_rate = Decimal(str(rates["GBP"]))

            with transaction.atomic():
                # Update or create the ExchangeRate entry with all required rates
                exchange_rate_entry, created = ExchangeRate.objects.update_or_create(
                    valuation_date=valuation_date,
                    defaults={
                        "chf_rate": chf_rate,
                        "usd_rate": usd_rate,
                        "gbp_rate": gbp_rate,
                    },
                )

                if created:
                    logger.info(f"Created new ExchangeRate entry for {valuation_date}.")
                else:
                    logger.info(f"Updated ExchangeRate entry for {valuation_date}.")

                # Cache the updated rates for quick access
                cache_key = f"exchange_rate_{valuation_date}"
                cache.set(
                    cache_key,
                    {
                        "chf_rate": float(exchange_rate_entry.chf_rate),
                        "usd_rate": float(exchange_rate_entry.usd_rate),
                        "gbp_rate": float(exchange_rate_entry.gbp_rate),
                    },
                    timeout=86400,
                )  # Cache for 24 hours

        except Exception as e:
            logger.error(f"Error storing exchange rates: {e}")


class TWRRCalculationState:
    def __init__(self):
        """
        Initializes the TWRRCalculationState with default values.
        """
        self.state = "Ready"
        self.twrr_series = None
        self.error_message = None
        self.exchanged_currency = None

    def process_request(
        self, source_currency, exchanged_currency, amount, start_date
    ) -> list:
        """
        Processes a TWRR calculation request.

        Parameters:
        - source_currency (str): The currency to convert from.
        - exchanged_currency (str): The currency to convert to.
        - amount (float): The amount to be converted.
        - start_date (date): The start date for the TWRR calculation.

        Returns:
        - list: A list of TWRR values or None if an error occurs.
        """
        ic(
            f"TWRRCalculationState: Processing TWRR from {start_date} until today for {source_currency} -> {exchanged_currency}."
        )
        logger.info(
            f"Processing TWRR from {start_date} until today for {source_currency} -> {exchanged_currency}."
        )
        self.state = "Processing Request"

        # Validate input dates
        if start_date >= date.today():  # Compare with today's date instead of end_date
            self.state = "Error"
            self.error_message = "start_date must be before today."
            logger.error(self.error_message)
            return None

        # Ensure exchanged_currency is not the same as the base currency
        if exchanged_currency == "EUR":
            self.state = "Error"
            self.error_message = (
                "Exchanged currency cannot be the same as the base currency (EUR)."
            )
            logger.error(self.error_message)
            return None

        try:
            # Set exchanged_currency
            self.exchanged_currency = exchanged_currency

            # Step 1: Retrieve historical exchange rates using HistoricalExchangeRateState
            state_box = HistoricalExchangeRateState()
            rates = state_box.fetch_historical_rates(
                source_currency, [start_date, date.today()]
            )
            ic(f"TWRRCalculationState: Rates: {rates}")
            if not rates:
                self.state = "Error"
                self.error_message = "Failed to retrieve historical exchange rates."
                logger.error(self.error_message)
                return None

            # Step 2: Calculate TWRR
            self.twrr_series = self.calculate_twrr(rates, amount)
            self.state = "Completed"
            logger.info("TWRR calculation completed successfully.")
            return self.twrr_series
        except Exception as e:
            self.state = "Error"
            self.error_message = str(e)
            logger.error(f"Error during TWRR calculation: {self.error_message}")
            return None

    def calculate_twrr(self, rates, amount) -> list:
        """
        Calculates the Time-Weighted Rate of Return (TWRR).

        Parameters:
        - rates (list): A list of historical exchange rates.
        - amount (float): The amount to be converted.

        Returns:
        - list: A list of TWRR values.
        """
        ic(
            f"TWRRCalculationState: Calculating TWRR for {self.exchanged_currency}. length of rates: {len(rates)}"
        )
        twrr_series = []

        for i in range(len(rates) - 1):
            ic(f"TWRRCalculationState: Iteration: {i}")
            # Extract rates from the 'rates' dictionary using the target currency
            try:
                start_rate = rates[i]["rates"][self.exchanged_currency]
                end_rate = rates[i + 1]["rates"][self.exchanged_currency]
                ic(
                    f"TWRRCalculationState: Start rate: {start_rate}, End rate: {end_rate}"
                )
            except KeyError:
                self.state = "Error"
                self.error_message = (
                    f"Missing exchange rate for {self.exchanged_currency} in data."
                )
                logger.error(self.error_message)
                return None

            if start_rate == 0:
                self.state = "Error"
                self.error_message = (
                    "Encountered a zero exchange rate, division by zero prevented."
                )
                logger.error(self.error_message)
                return None

            twrr = (end_rate / start_rate) - 1
            twrr_series.append(
                {
                    "valuation_date": rates[i + 1][
                        "date"
                    ],  # Use 'date' instead of 'valuation_date'
                    "twrr": twrr,
                }
            )

        return twrr_series


class ProviderManagementState:
    def __init__(self):
        """
        Initializes the ProviderManagementState with default values.
        """
        self.state = "Ready"
        self.error_message = None

    def update_priority(self, provider_id, new_priority) -> dict:
        """
        Updates the priority of a provider and dynamically reorders other providers.
        Ensures that priorities remain unique and properly ordered.

        Parameters:
        - provider_id (int): The ID of the provider to update.
        - new_priority (int): The new priority to assign to the provider.

        Returns:
        - dict: A dictionary with provider details or None if an error occurs.
        """
        self.state = "Processing Request"
        logger.info(f"Updating priority for provider {provider_id} to {new_priority}.")

        try:
            with transaction.atomic():
                # Fetch the provider to update
                provider = Provider.objects.get(id=provider_id, active=True)
                current_priority = provider.priority

                # Validate the new priority
                max_priority = Provider.objects.filter(active=True).count()
                if new_priority < 1 or new_priority > max_priority:
                    self.state = "Error"
                    self.error_message = f"Invalid priority: {new_priority}. Must be between 1 and {max_priority}."
                    logger.error(self.error_message)
                    return None

                # If the new priority is the same, no update is needed
                if current_priority == new_priority:
                    self.state = "Completed"
                    return {
                        "id": provider.id,
                        "name": provider.name,
                        "priority": provider.priority,
                    }

                # Adjust priorities for other providers
                if current_priority < new_priority:
                    Provider.objects.filter(
                        priority__gt=current_priority,
                        priority__lte=new_priority,
                        active=True,
                    ).update(priority=models.F("priority") - 1)
                else:
                    Provider.objects.filter(
                        priority__gte=new_priority,
                        priority__lt=current_priority,
                        active=True,
                    ).update(priority=models.F("priority") + 1)

                # Update the target provider's priority
                provider.priority = new_priority
                provider.save()

                self.state = "Completed"
                logger.info(
                    f"Provider {provider.name} updated to priority {new_priority}."
                )
                return {
                    "id": provider.id,
                    "name": provider.name,
                    "new_priority": provider.priority,
                }

        except Provider.DoesNotExist:
            self.state = "Error"
            self.error_message = (
                f"Provider with ID {provider_id} not found or inactive."
            )
            logger.error(self.error_message)
            return None
        except Exception as e:
            self.state = "Error"
            self.error_message = str(e)
            logger.error(f"Error while updating priority: {self.error_message}")
            return None

    def reorder_priorities(self) -> None:
        """
        Ensures that provider priorities remain sequential and unique.
        Useful when manually modifying priorities or after batch updates.
        """
        logger.info("Reordering provider priorities to maintain consistency.")
        try:
            with transaction.atomic():
                providers = Provider.objects.filter(active=True).order_by("priority")
                for index, provider in enumerate(providers, start=1):
                    provider.priority = index
                    provider.save()
            logger.info("Provider priorities successfully reordered.")
        except Exception as e:
            logger.error(f"Error while reordering priorities: {e}")


class HistoricalExchangeRateState:
    def __init__(self):
        """
        Initializes the HistoricalExchangeRateState with default values.
        """
        self.state = "Ready"
        self.historical_rates = None
        self.error_message = None
        self.SUPPORTED_CURRENCIES = ["USD", "EUR", "CHF", "GBP"]

    def fetch_historical_rates(self, base_currency, date_range) -> list:
        """
        Retrieves historical exchange rates from cache, database, or an external provider.
        If a provider fails, the system tries the next one in priority order.

        Parameters:
        - base_currency (str): The base currency for the rates.
        - date_range (list): A list containing the start and end dates for the rates.

        Returns:
        - list: A list of historical exchange rates or None if an error occurs.
        """
        self.state = "Processing Request"
        logger.info(
            f"Fetching historical exchange rates for {base_currency} from {date_range[0]} to {date_range[-1]}."
        )

        # Step 1: Check cache for historical rates
        cached_rates = self.get_cached_rates(base_currency, date_range)
        if cached_rates:
            ic(f"Cached rates: {cached_rates}")
            self.state = "Completed"
            logger.info("Returning cached historical exchange rates.")
            return cached_rates

        # Step 2: Fetch from the database
        db_rates = self.get_historical_rates_from_db(base_currency, date_range)
        if db_rates:
            self.state = "Completed"
            ic(f"Database rates: {db_rates}")
            logger.info("Returning database-stored historical exchange rates.")
            return db_rates

        # Step 3: Fetch from external providers if data is unavailable
        self.state = "Fetching External Data"
        external_rates = self.fetch_external_rates(base_currency, date_range)

        if external_rates:
            self.state = "Completed"
            logger.info(
                "Fetched historical exchange rates from external provider and stored them."
            )
            return external_rates
        else:
            self.state = "Error"
            self.error_message = "Failed to retrieve historical exchange rates."
            logger.error(self.error_message)
            return None

    def get_cached_rates(self, base_currency, date_range) -> list:
        """
        Retrieves cached historical exchange rates if available.

        Parameters:
        - base_currency (str): The base currency for the rates.
        - date_range (list): A list containing the start and end dates for the rates.

        Returns:
        - list: A list of cached historical exchange rates or None if not found.
        """
        cache_key = f"historical_rates_{base_currency}_{date_range[0]}_{date_range[-1]}"
        cached_data = cache.get(cache_key)
        return cached_data if cached_data else None

    def get_historical_rates_from_db(self, base_currency, date_range) -> list:
        """
        Retrieves historical exchange rates from the database.

        Parameters:
        - base_currency (str): The base currency for the rates.
        - date_range (list): A list containing the start and end dates for the rates.

        Returns:
        - list: A list of historical exchange rates or None if not found.
        """
        ic(
            f"Getting historical rates from database for {base_currency} from {date_range[0]} to {date_range[-1]}."
        )
        try:
            rates = ExchangeRate.objects.filter(
                valuation_date__range=[date_range[0], date_range[-1]],
            ).order_by("valuation_date")

            if not rates.exists():
                return None

            result = []
            for rate in rates:
                rate_dict = {
                    "valuation_date": rate.valuation_date.strftime("%Y-%m-%d"),
                    "rates": {
                        symbol: getattr(rate, f"{symbol.lower()}_rate")
                        for symbol in self.SUPPORTED_CURRENCIES
                    },
                }
                result.append(rate_dict)

            # Store results in cache
            cache_key = (
                f"historical_rates_{base_currency}_{date_range[0]}_{date_range[-1]}"
            )
            cache.set(cache_key, result, timeout=86400)  # Cache for 24 hours

            return result
        except Exception as e:
            logger.error(f"Error retrieving historical rates from the database: {e}")
            return None

    def fetch_external_rates(self, base_currency, date_range) -> list:
        """
        Fetches historical exchange rates from the highest-priority provider.
        If the first provider fails, it tries the next one in priority order.

        Parameters:
        - base_currency (str): The base currency for the rates.
        - date_range (list): A list containing the start and end dates for the rates.

        Returns:
        - list: A list of historical exchange rates or None if not found.
        """
        ic(
            f"Fetching external rates for {base_currency} from {date_range[0]} to {date_range[-1]}."
        )
        providers = Provider.objects.filter(active=True).order_by("priority")
        rates = []

        if not providers.exists():
            logger.error("No active providers available.")
            return None
        ic(f"Date range: {date_range}")

        # Generate all dates in the range
        start_date, end_date = date_range
        all_dates = [
            start_date + timedelta(days=x)
            for x in range((end_date - start_date).days + 1)
        ]

        for provider in providers:
            try:
                adapter = load_adapter(provider)
                for date in all_dates:  # Use all_dates instead of date_range
                    rate_data = adapter.get_exchange_rates(
                        base_currency=base_currency,
                        date=date.strftime("%Y-%m-%d"),
                        provider=provider,
                    )
                    if rate_data:
                        rates.append(rate_data)

                # Store fetched data in the database and cache
                self.store_historical_rates_in_db(base_currency, rates)
                cache_key = (
                    f"historical_rates_{base_currency}_{date_range[0]}_{date_range[-1]}"
                )
                cache.set(cache_key, rates, timeout=86400)  # Cache for 24 hours

                return rates
            except Exception as e:
                logger.warning(
                    f"Provider {provider.name} failed to fetch historical rates: {e}"
                )
                continue  # Try the next provider

        return None

    def store_historical_rates_in_db(self, base_currency, rates) -> None:
        """
        Saves fetched exchange rates into the database.

        Parameters:
        - base_currency (str): The base currency for the rates.
        - rates (list): A list of historical exchange rates.
        """
        try:
            for rate in rates:
                valuation_date = rate["date"]
                ExchangeRate.objects.update_or_create(
                    valuation_date=valuation_date,
                    defaults={
                        "chf_rate": rate["rates"].get("CHF"),
                        "usd_rate": rate["rates"].get("USD"),
                        "gbp_rate": rate["rates"].get("GBP"),
                    },
                )
            logger.info(
                "Historical exchange rates successfully stored in the database."
            )
        except Exception as e:
            logger.error(f"Error storing historical exchange rates: {e}")

    def store_exchange_rates(self, rates, valuation_date=None) -> None:
        """
        Stores the fetched exchange rates in the database and cache for future use.

        Parameters:
        - rates (dict): A dictionary containing all required exchange rates relative to EUR.
          Example:
            {
                'CHF': 0.940122,
                'USD': 1.033218,
                'GBP': 0.833213
            }
        - valuation_date (date, optional): The date of the exchange rates. Defaults to today.
        """
        try:
            valuation_date = valuation_date or date.today()

            # Validate that all required rates are present
            required_currencies = ["CHF", "USD", "GBP"]
            missing_currencies = [
                currency for currency in required_currencies if currency not in rates
            ]

            if missing_currencies:
                logger.error(f"Missing rates for: {', '.join(missing_currencies)}")
                raise ValueError(f"Missing rates for: {', '.join(missing_currencies)}")

            # Convert rates to Decimal to ensure proper storage
            chf_rate = Decimal(str(rates["CHF"]))
            usd_rate = Decimal(str(rates["USD"]))
            gbp_rate = Decimal(str(rates["GBP"]))

            with transaction.atomic():
                # Update or create the ExchangeRate entry with all required rates
                exchange_rate_entry, created = ExchangeRate.objects.update_or_create(
                    valuation_date=valuation_date,
                    defaults={
                        "chf_rate": chf_rate,
                        "usd_rate": usd_rate,
                        "gbp_rate": gbp_rate,
                    },
                )

                if created:
                    logger.info(f"Created new ExchangeRate entry for {valuation_date}.")
                else:
                    logger.info(f"Updated ExchangeRate entry for {valuation_date}.")

                # Cache the updated rates for quick access
                cache_key = f"exchange_rate_{valuation_date}"
                cache.set(
                    cache_key,
                    {
                        "chf_rate": float(exchange_rate_entry.chf_rate),
                        "usd_rate": float(exchange_rate_entry.usd_rate),
                        "gbp_rate": float(exchange_rate_entry.gbp_rate),
                    },
                    timeout=86400,
                )  # Cache for 24 hours

        except Exception as e:
            logger.error(f"Error storing exchange rates: {e}")
