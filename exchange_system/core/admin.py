from django import forms
from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from django.http import JsonResponse
from core.models import Currency, ExchangeRate, Provider
from core.state_boxes import CurrencyConversionState
from decimal import Decimal
from icecream import ic
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

logger = logging.getLogger("core")

# Register models in Django Admin
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol")


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("valuation_date", "chf_rate", "usd_rate", "gbp_rate")
    list_filter = ("valuation_date",)

    # Añadir vistas personalizadas
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "currency-converter/",
                self.admin_site.admin_view(self.currency_converter_view),
                name="currency_converter",
            ),
            path(
                "exchange-rate-graph/",
                self.admin_site.admin_view(self.exchange_rate_graph_view),
                name="exchange_rate_graph",
            ),
        ]
        return custom_urls + urls

    # --------------------------- Currency Converter View --------------------------- #
    class CurrencyConverterForm(forms.Form):
        source_currency = forms.ChoiceField(
            choices=[("EUR", "EUR"), ("USD", "USD"), ("CHF", "CHF"), ("GBP", "GBP")]
        )
        target_currencies = forms.MultipleChoiceField(
            choices=[("EUR", "EUR"), ("USD", "USD"), ("CHF", "CHF"), ("GBP", "GBP")],
            required=True,
        )
        amount = forms.DecimalField(decimal_places=2, max_digits=10)

    def currency_converter_view(self, request):
        converted_data = None
        form = self.CurrencyConverterForm(request.POST or None)

        if request.method == "POST" and form.is_valid():
            source_currency = form.cleaned_data["source_currency"]
            target_currencies = form.cleaned_data["target_currencies"]
            amount = form.cleaned_data["amount"]

            state = CurrencyConversionState()
            converted_data = {
                currency: state.process_request(source_currency, currency, amount, date=None)
                for currency in target_currencies
            }

        context = {
            "form": form,
            "converted_data": converted_data,
            "title": "Currency Converter",
            **self.admin_site.each_context(request),
        }
        return render(request, "admin/currency_converter.html", context)

    # --------------------------- Exchange Rate Graph View --------------------------- #
    def exchange_rate_graph_view(self, request):
        currency_options = [("EUR", "EUR"), ("USD", "USD"), ("CHF", "CHF"), ("GBP", "GBP")]
        ic("Request received")
        ic(request.headers)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            ic("Request is AJAX")
            selected_currencies = request.GET.getlist("currencies")
            ic(selected_currencies)
            # Exclude EUR from selected currencies as it's the base currency
            selected_currencies = [c for c in selected_currencies if c != "EUR"]

            if not selected_currencies:
                ic("No valid currencies selected")
                return JsonResponse({"error": "No valid currencies selected"}, status=400)

            # Map currencies to their respective fields in the database
            currency_field_map = {
                "USD": "usd_rate",
                "CHF": "chf_rate",
                "GBP": "gbp_rate",
            }

            data = {}
            labels_set = set()  # Usamos un conjunto para evitar duplicados de fechas

            for currency in selected_currencies:
                field_name = currency_field_map.get(currency)
                if field_name:
                    rates = list(ExchangeRate.objects.all().values_list("valuation_date", field_name))
                    logger.debug(f"Rates for {currency}: {rates}")
                    data[currency] = rates

                    # Extraer fechas para el eje X
                    labels_set.update(rate[0] for rate in rates)

            labels = sorted(labels_set) # Extraer todas las fechas únicas
            return JsonResponse({"data": data, "labels": labels})

        context = {
            "currency_options": currency_options,
            "title": "Exchange Rate Graph",
            **self.admin_site.each_context(request),
        }
        return render(request, "admin/exchange_rate_graph.html", context)


class ProviderAdminForm(forms.ModelForm):
    api_key = forms.CharField(required=False, widget=forms.PasswordInput(), label="API Key (enter new)")

    class Meta:
        model = Provider
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data['api_key']:  # Solo cifrar si se proporciona una nueva API key
            instance.set_api_key(self.cleaned_data['api_key'])
        if commit:
            instance.save()
        return instance

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    form = ProviderAdminForm
    list_display = ('name', 'priority', 'active', "last_failure")
    search_fields = ("name",)
    list_filter = ("active",)
    ordering = ("priority",)
    readonly_fields = ('show_api_key', "last_failure")

    def show_api_key(self, obj):
        """Muestra un mensaje indicando que la clave está almacenada."""
        return "API Key stored" if obj._api_key else "Not configured"
    show_api_key.short_description = "API Key Status"

class CustomAdminSite(admin.AdminSite):
    site_header = "Currency Exchange Admin"
    site_title = "Currency Exchange Admin Portal"
    index_title = "Welcome to the Currency Exchange Admin"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('currency-converter/', self.admin_view(self.currency_converter_view), name='currency_converter'),
            path('exchange-rate-graph/', self.admin_view(self.exchange_rate_graph_view), name='exchange_rate_graph'),
        ]
        return custom_urls + urls

    def currency_converter_view(self, request):
        class CurrencyConverterForm(forms.Form):
            source_currency = forms.ChoiceField(
                choices=[("EUR", "EUR"), ("USD", "USD"), ("CHF", "CHF"), ("GBP", "GBP")]
            )
            target_currencies = forms.MultipleChoiceField(
                choices=[("EUR", "EUR"), ("USD", "USD"), ("CHF", "CHF"), ("GBP", "GBP")],
                required=True,
            )
            amount = forms.DecimalField(decimal_places=2, max_digits=10)

        converted_data = None
        form = CurrencyConverterForm(request.POST or None)

        if request.method == "POST" and form.is_valid():
            source_currency = form.cleaned_data["source_currency"]
            target_currencies = form.cleaned_data["target_currencies"]
            amount = form.cleaned_data["amount"]

            state = CurrencyConversionState()
            converted_data = {
                currency: state.process_request(source_currency, currency, amount)
                for currency in target_currencies
            }

        context = {
            "form": form,
            "converted_data": converted_data,
            "title": "Currency Converter",
            **self.each_context(request),
        }
        return render(request, "currency_converter.html", context)

    def exchange_rate_graph_view(self, request):
        currency_options = [("EUR", "EUR"), ("USD", "USD"), ("CHF", "CHF"), ("GBP", "GBP")]

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            selected_currencies = request.GET.getlist("currencies")

            # Exclude EUR from selected currencies as it's the base currency
            selected_currencies = [c for c in selected_currencies if c != "EUR"]

            if not selected_currencies:
                return JsonResponse({"error": "No valid currencies selected"}, status=400)

            # Map currencies to their respective fields in the database
            currency_field_map = {
                "USD": "usd_rate",
                "CHF": "chf_rate",
                "GBP": "gbp_rate",
            }

            data = {}
            labels_set = set()  # Usamos un conjunto para evitar duplicados de fechas
            for currency in selected_currencies:
                field_name = currency_field_map.get(currency)
                if field_name:
                    rates = list(ExchangeRate.objects.all().values_list("valuation_date", field_name))
                    ic(f"Rates for {currency}: {rates}")  # Depuración
                    data[currency] = rates

                    labels_set.update(rate[0] for rate in rates)  # Extraer fechas

            labels = sorted(labels_set)  # Convertir a lista y ordenar
            ic("Final labels:", labels)  # Depuración

            return JsonResponse({"data": data, "labels": labels})

        context = {
            "currency_options": currency_options,
            "title": "Exchange Rate Graph",
            **self.each_context(request),
        }
        return render(request, "exchange_rate_graph.html", context)


# Instantiate the custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')

# Register your models with the custom admin site
custom_admin_site.register(Currency)
custom_admin_site.register(ExchangeRate)
custom_admin_site.register(Provider)
