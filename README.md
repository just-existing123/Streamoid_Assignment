# Product Catalog Management API

This is a backend service that allows sellers to manage their product catalogs through CSV file uploads and provides APIs for viewing and filtering products.

## Features

- CSV file upload and validation
- Product data storage in SQLite database
- REST APIs for listing and searching products
- Pagination support
- Search filters by brand, color, and price range

## Technical Stack

- Python 3.8+
- FastAPI (Web Framework)
- SQLAlchemy (ORM)
- Pandas (CSV Processing)
- SQLite (Database)
- Pydantic (Data Validation)

## Setup Instructions

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

The server will start at http://localhost:8000

## API Documentation

### Upload Products (CSV)

```
POST /upload
Content-Type: multipart/form-data
```

Example:
```bash
curl -X POST -F "file=@products.csv" http://localhost:8000/upload
```

### List Products

```
GET /products?page=1&limit=10
```

Parameters:
- page: Page number (default: 1)
- limit: Items per page (default: 10)

### Search Products

```
GET /products/search
```

Parameters:
- brand: Filter by brand name
- color: Filter by color
- min_price: Minimum price
- max_price: Maximum price

Example:
```bash
GET /products/search?brand=StreamThreads&maxPrice=2000
```

## Testing

To run the tests:
```bash
pytest
```

## CSV File Format

The CSV file should have the following columns:
- sku (required)
- name (required)
- brand (required)
- color
- size
- mrp (required)
- price (required)
- quantity (required)

Validation rules:
- price must be less than or equal to mrp
- quantity must be non-negative
- All required fields must be present