from pydantic import BaseModel, Field
from typing import List

class HistoricalRateResponse(BaseModel):
    """
    Represents the exchange rates for a specific date.
    
    Attributes:
        valuation_date (str): The date for which the rates are applicable.
        chf_rate (float): The exchange rate from EUR to CHF.
        usd_rate (float): The exchange rate from EUR to USD.
        gbp_rate (float): The exchange rate from EUR to GBP.
    """
    valuation_date: str
    chf_rate: float = Field(..., description="Rate from EUR to CHF")
    usd_rate: float = Field(..., description="Rate from EUR to USD")
    gbp_rate: float = Field(..., description="Rate from EUR to GBP")

class HistoricalRatesResponse(BaseModel):
    """
    Represents a collection of historical exchange rates.
    
    Attributes:
        exchange_rates (List[HistoricalRateResponse]): A list of historical exchange rate data.
    """
    exchange_rates: List[HistoricalRateResponse]
