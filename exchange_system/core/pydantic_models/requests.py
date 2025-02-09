from pydantic import BaseModel, Field
from datetime import date

class HistoricalRateRequest(BaseModel):
    """
    Request model for fetching historical exchange rates.

    Attributes:
        base_currency (str): The base currency code (e.g., 'USD').
        date_from (date): The start date for the historical data.
        date_to (date): The end date for the historical data.
    """
    base_currency: str
    date_from: date
    date_to: date

class ProviderPriorityUpdateRequest(BaseModel):
    """
    Request model for updating the priority of a provider.

    Attributes:
        provider_id (int): The ID of the provider, must be greater than 0.
        new_priority (int): The new priority value for the provider, must be greater than 0.
    """
    provider_id: int = Field(..., gt=0, description="ID of the provider")
    new_priority: int = Field(..., gt=0, description="New priority value for the provider")

class TWRRRequest(BaseModel):
    """
    Request model for calculating the Time-Weighted Rate of Return (TWRR).

    Attributes:
        base_currency (str): The base currency code (e.g., 'EUR').
        target_currency (str): The target currency code (e.g., 'USD').
        amount (float): The investment amount, must be greater than 0.
        start_date (date): The start date for the TWRR calculation.
        end_date (date): The end date for the TWRR calculation.
    """
    base_currency: str = Field(..., description="Base currency (e.g., EUR)")
    target_currency: str = Field(..., description="Target currency (e.g., USD)")
    amount: float = Field(..., gt=0, description="Investment amount")
    start_date: date
    end_date: date
