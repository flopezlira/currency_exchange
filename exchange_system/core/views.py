from datetime import datetime

from icecream import ic
from pydantic import ValidationError
from rest_framework import generics, serializers, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pydantic_models.exchange_rates import ExchangeRateModel
from core.pydantic_models.requests import HistoricalRateRequest

from .models import Currency, ExchangeRate, Provider
from .pydantic_models.requests import ProviderPriorityUpdateRequest
from .serializers import (
    CurrencyConversionSerializer,
    CurrencySerializer,
    ExchangeRateListSerializer,
    ExchangeRateSerializer,
    ProviderSerializer,
    TWRRRequestSerializer,
)
from .state_boxes import CurrencyConversionState  # ExternalExchangeRateState,
from .state_boxes import (
    HistoricalExchangeRateState,
    ProviderManagementState,
    TWRRCalculationState,
)


class CurrencyConversionView(APIView):
    """
    API view to handle currency conversion requests.
    """

    def post(self, request) -> Response:
        """
        Processes a currency conversion request.
        """
        # Validate the incoming request data
        serializer = CurrencyConversionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        source_currency = validated_data["source_currency"]
        target_currency = validated_data["target_currency"]
        amount = validated_data["amount"]

        try:
            # Initialize the state box for currency conversion
            state_box = CurrencyConversionState()
            converted_amount = state_box.process_request(
                source_currency, target_currency, amount
            )

            # Check for errors in the state box
            if state_box.state == "Error":
                return Response(
                    {"error": state_box.error_message},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Return the conversion result
            return Response(
                {
                    "source_currency": source_currency,
                    "target_currency": target_currency,
                    "amount": amount,
                    "converted_amount": converted_amount,
                    "exchange_rate": state_box.exchange_rate,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            # Handle any unexpected exceptions
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CurrencyListView(generics.ListCreateAPIView):
    """
    API view to list and create currencies.
    """
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer


class CurrencyDetailView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve and update a specific currency.
    """
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer


# ExchangeRate APIs


class ExchangeRateListView(generics.ListAPIView):
    """
    Retrieves a list of currency rates for a specific time period.
    Parameters: source_currency, date_from, date_to
    Returns: A time series list of rate values for each available currency.
    """

    serializer_class = ExchangeRateListSerializer

    def list(self, request, *args, **kwargs) -> Response:
        """
        Handles the GET request to list exchange rates.
        """
        source_currency = request.query_params.get("source_currency")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        # Validate required parameters
        if not source_currency or not date_from or not date_to:
            return Response(
                {"error": "Missing required parameters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Parse date parameters
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch historical exchange rates
        state_box = HistoricalExchangeRateState()
        rates = state_box.fetch_historical_rates("EUR", [date_from, date_to])

        # Check for errors in the state box
        if state_box.state == "Error":
            return Response(
                {"error": state_box.error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Structure the response data
        response_data = {
            "exchange_rates": rates
        }  # Adjusted to match the serializer

        return Response(response_data, status=status.HTTP_200_OK)


class ProviderListView(generics.ListCreateAPIView):
    """
    API view to list and create providers.
    """
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer


class ProviderDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a specific provider.
    """
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer


class CurrencyDetailView(RetrieveAPIView):
    """
    API view to retrieve a specific currency by its code.
    """
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    lookup_field = "code"


class TWRRView(APIView):
    """
    API view to handle TWRR (Time-Weighted Rate of Return) calculation requests.
    """

    def post(self, request) -> Response:
        """
        Processes a TWRR calculation request.
        """
        # Validate the incoming request data
        serializer = TWRRRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        source_currency = validated_data["source_currency"]
        exchanged_currency = validated_data["exchanged_currency"]
        amount = validated_data["amount"]
        start_date = validated_data["start_date"]

        try:
            # Initialize the state box for TWRR calculation
            state_box = TWRRCalculationState()
            ic(f"Source currency: {source_currency}")
            ic(f"Exchanged currency: {exchanged_currency}")
            ic(f"Amount: {amount}")
            ic(f"Start date: {start_date}")
            twrr_series = state_box.process_request(
                source_currency, exchanged_currency, amount, start_date
            )
            ic(f"TWRR series: {twrr_series}")

            # Check for errors in the state box
            if state_box.state == "Error":
                return Response(
                    {"error": state_box.error_message},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Return the TWRR series
            return Response({"twrr_series": twrr_series}, status=status.HTTP_200_OK)
        except Exception as e:
            # Handle any unexpected exceptions
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProviderListView(generics.ListAPIView):
    """
    Lists all providers sorted by priority.
    """

    queryset = Provider.objects.all().order_by("priority")
    serializer_class = ProviderSerializer


class FetchHistoricalExchangeRatesView(APIView):
    """
    API endpoint to fetch historical exchange rates for a given date.
    """

    def get(self, request) -> Response:
        """
        Handles the GET request to fetch historical exchange rates.
        """
        try:
            date = request.query_params.get("date")
            if not date:
                return Response(
                    {"error": "Date parameter is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch historical exchange rates
            state_box = HistoricalExchangeRateState()
            rates = state_box.fetch_historical_rates(
                "EUR", ["USD", "CHF", "GBP"], [date]
            )

            # Check for errors in the state box
            if state_box.state == "Error":
                return Response(
                    {"error": state_box.error_message},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Return the fetched rates
            return Response(
                {
                    "message": "Historical exchange rates fetched successfully.",
                    "rates": rates,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            # Handle any unexpected exceptions
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
