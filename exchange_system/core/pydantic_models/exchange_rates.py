from pydantic import BaseModel, Field
from datetime import date

class ExchangeRateModel(BaseModel):
    """
    ExchangeRateModel represents the exchange rates for a specific valuation date.
    
    Attributes:
        valuation_date (date): The date for which the exchange rates are applicable.
        chf_rate (float): The exchange rate from EUR to CHF. Must be greater than 0.
        usd_rate (float): The exchange rate from EUR to USD. Must be greater than 0.
        gbp_rate (float): The exchange rate from EUR to GBP. Must be greater than 0.
    """
    valuation_date: date  # The date for which the exchange rates are applicable
    chf_rate: float = Field(..., gt=0, description="Rate from EUR to CHF")  # Exchange rate from EUR to CHF
    usd_rate: float = Field(..., gt=0, description="Rate from EUR to USD")  # Exchange rate from EUR to USD
    gbp_rate: float = Field(..., gt=0, description="Rate from EUR to GBP")  # Exchange rate from EUR to GBP
