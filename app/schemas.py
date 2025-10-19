from pydantic import BaseModel, field_validator
from typing import List, Optional

class ProductBase(BaseModel):
    sku: str
    name: str
    brand: str
    color: Optional[str] = None
    size: Optional[str] = None
    mrp: float
    price: float
    quantity: int

    @field_validator('price')
    def price_must_be_less_than_mrp(cls, v, values):
        if 'mrp' in values.data and v > values.data['mrp']:
            raise ValueError('Price must be less than or equal to MRP')
        return v

    @field_validator('quantity')
    def quantity_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Quantity must be non-negative')
        return v

class Product(ProductBase):
    class Config:
        from_attributes = True
        populate_by_name = True

class UploadResponse(BaseModel):
    stored: int
    failed: List[str]