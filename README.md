# MyCurrency - Currency Exchange Platform
Developed by Francisco López-Lira Hinojo
Email: flopezlira@gmail.com

## Introduction

MyCurrency is a web platform that provides currency exchange rate calculations using multiple external providers. The system is designed to be flexible and supports pluggable providers that can be dynamically prioritized.

The platform implements:
- **Adapter Design Pattern** for provider integration.
- **Pluggable providers**: Easily add new providers via Django admin without the need to restart the system.
- **Resilient provider selection**: If one provider fails, the system automatically switches to the next based on priority.
- **Developed using CleanRoom Software Engineering methodology**, utilizing state machines for handling requests.
- **Django 4** and **Python 3** as the core technology stack.
- **Django Rest Framework (DRF)** to expose a robust REST API.
- **drf-spectacular** for API schema generation and documentation.
- **JWT Authentication** for securing API access.

## Features

- **Retrieve historical exchange rates** for a given period.
- **Convert amounts** between different currencies using the latest available exchange rates.
- **Compute time-weighted rate of return (TWRR)** for investments in different currencies.
- **Admin panel** for managing currency conversions and exchange rate visualizations.
- **API documentation** available at `api/docs/` (excluding admin endpoints).

## API Endpoints

### Public Endpoints
1. **Retrieve List of Currencies**  
   `GET /currencies/`  
   **Response**: A list of available currencies.

2. **Retrieve Currency Details**  
   `GET /currencies/<currency_code>/`  
   **Response**: Details of the specified currency.

3. **Retrieve Historical Exchange Rates**  
   `GET /exchange-rates/`  
   **Parameters**:  
   - `source_currency`: Base currency (defaults to **EUR** for efficiency).  
   - `date_from`: Start date.  
   - `date_to`: End date.  
   **Response**: A time series of exchange rates.  
   **State Machine**: `ExchangeRateListView -> HistoricalExchangeRateState`.

4. **Convert Currency Amount**  
   `GET /conversions/`  
   **Parameters**:  
   - `source_currency`: Currency to convert from.  
   - `amount`: Amount to convert.  
   - `exchanged_currency`: Target currency.  
   **Response**: Converted amount.  
   **State Machine**: `CurrencyConversionView -> CurrencyConversionState`.

5. **Compute Time-Weighted Rate of Return (TWRR)**  
   `GET /twrr/`  
   **Parameters**:  
   - `source_currency`: Original currency.  
   - `amount`: Invested amount.  
   - `exchanged_currency`: Target currency.  
   - `start_date`: Investment start date.  
   **Response**: Historical TWRR values.

### Authentication & Admin Endpoints
1. **Token Authentication (JWT)**  
   - `POST /api/token/` → Obtain access and refresh tokens.  
   - `POST /api/token/refresh/` → Refresh access token.  

2. **Admin Panel**  
   - `GET /admin/` → Access Django’s custom admin panel.  
   - `GET /admin/currency-converter/` → Calculate currency conversion in the Admin interface.  
   - `GET /admin/exchange-rate-graph/` → Visualize exchange rate trends.

3. **API Documentation**  
   - `GET /api/schema/` → OpenAPI schema endpoint.  
   - `GET /api/docs/` → Swagger UI for interactive API exploration.  

## Installation & Setup

### Preconditions

1. Clone the repository:
   ```sh
   git clone <repository_url>
   cd mycurrency
   ```
2. Create and activate a virtual environment:
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Create and configure the environment file:
   ```sh
   cp env.development .env
   ```

   The `.env` file should contain the following configurations:

   ```ini
   ENVIRONMENT=development
   SECRET_KEY="your-secret-key"

   DB_ENGINE=django.db.backends.mysql
   # Or use SQLite
   # DB_ENGINE=django.db.backends.sqlite3
   DB_NAME="your_database_name"
   DB_USER="your_database_user"
   DB_PASSWORD="your_database_password"
   DB_HOST="your_database_host"
   DB_PORT="your_database_port"

   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   FIXER_API_KEY="your_api_key"
   ```

   For different environments, create separate `.env` files:
   - **`.env.testing`** for test environments.
   - **`.env.production`** for production settings.

5. Run migrations:
   ```sh
   python manage.py migrate
   ```
6. Create a superuser:
   ```sh
   python manage.py createsuperuser
   ```
7. Start the development server:
   ```sh
   python manage.py runserver
   ```

## Configuration

- **Creating Currencies**:  
  Use the Django admin panel (`/admin/`) to add available currencies (EUR, USD, GBP, etc.).

- **Adding Providers**:  
  1. Go to `/admin//core/provider/`  
  2. Create a new provider with API details.  
  3. Add the corresponding provider adapter data.  

- **Changing Provider Priority**:  
  Providers can be prioritized dynamically through the admin interface.

## Optimization: Using EUR as the Base Currency

To improve query performance and reduce the number of stored records, **EUR has been chosen as the base currency** for exchange rate calculations. This means:
- All rates are stored relative to **EUR**.
- Queries require fewer calculations when retrieving rates.
- The system remains adaptable to multiple providers while maintaining efficiency.

## Best practices
- **Code Formatting**: Uses `isort` and `black` for consistent formatting.
- **Data Validation**: Utilizes `pydantic` for request validation.

## Improvements & Future Enhancements

- **Cache Optimization**: Implement **Redis** for caching exchange rates and improving response times.

---

For further details, please refer to the API documentation at `/api/docs/`.
```
