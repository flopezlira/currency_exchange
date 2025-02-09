from django.urls import path

from .views import (
    CurrencyConversionView,
    CurrencyDetailView,
    CurrencyListView,
    ExchangeRateListView,
    ProviderDetailView,
    ProviderListView,
    TWRRView,
)

urlpatterns = [
    # Currency endpoints
    path("currencies/", CurrencyListView.as_view(), name="currency-list"),
    path(
        "currencies/<str:code>/",
        CurrencyDetailView.as_view(),
        name="currency-detail",
    ),
    # ExchangeRate endpoints
    path(
        "exchange-rates/", ExchangeRateListView.as_view(), name="exchange-rate-list"
    ),
    # Provider endpoints
    path("providers/", ProviderListView.as_view(), name="provider-list"),
    path(
        "providers/<int:pk>/", ProviderDetailView.as_view(), name="provider-detail"
    ),
    path(
        "conversions/", CurrencyConversionView.as_view(), name="currency-conversion"
    ),
    path("twrr/", TWRRView.as_view(), name="twrr-calculation"),
]
