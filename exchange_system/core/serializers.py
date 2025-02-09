from datetime import datetime

from rest_framework import serializers

from .models import Currency, ExchangeRate, Provider


class CurrencySerializer(serializers.ModelSerializer):
    """
    Serializer for the Currency model.
    """
    class Meta:
        model = Currency
        fields = ["id", "code", "name", "symbol"]


class ExchangeRateSerializer(serializers.ModelSerializer):
    """
    Serializer for the ExchangeRate model.
    """
    class Meta:
        model = ExchangeRate
        fields = [
            "id",
            "valuation_date",
            "chf_rate",
            "usd_rate",
            "gbp_rate",
        ]


class ProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for the Provider model.
    """
    class Meta:
        model = Provider
        fields = ["id", "name", "adapter_path", "priority", "active"]


class CurrencyConversionSerializer(serializers.Serializer):
    """
    Serializer for currency conversion requests.
    """
    source_currency = serializers.CharField()
    target_currency = serializers.CharField()
    amount = serializers.FloatField(min_value=0.01)
    date = serializers.DateField()

    def validate_date(self, value):
        """
        Validate that the date is not in the future.
        """
        if value > datetime.now().date():
            raise serializers.ValidationError("Date cannot be in the future.")
        return value


class ExchangeRateDataSerializer(serializers.Serializer):
    """
    Serializer for exchange rate data.
    """
    timestamp = serializers.IntegerField()
    date = serializers.DateField()
    base = serializers.CharField()
    rates = serializers.DictField(child=serializers.FloatField())


class ExchangeRateListSerializer(serializers.Serializer):
    """
    Serializer for a list of exchange rate data.
    """
    exchange_rates = serializers.ListField(
        child=serializers.ListField(child=ExchangeRateDataSerializer())
    )


class TWRRRequestSerializer(serializers.Serializer):
    """
    Serializer for Time-Weighted Rate of Return (TWRR) requests.
    """
    source_currency = serializers.CharField(max_length=3)
    exchanged_currency = serializers.CharField(max_length=3)
    amount = serializers.DecimalField(max_digits=18, decimal_places=6)
    start_date = serializers.DateField()
