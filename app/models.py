from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Product(Base):
    __tablename__ = "products"

    sku = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    color = Column(String)
    size = Column(String)
    mrp = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)