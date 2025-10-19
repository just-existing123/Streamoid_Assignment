import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models, schemas
import io

async def process_csv(file: UploadFile, db: Session):
    # Read the CSV file
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}")

    # Validate column names
    required_columns = ['sku', 'name', 'brand', 'mrp', 'price', 'quantity']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    stored = 0
    failed = []
    
    # Process each row
    for index, row in df.iterrows():
        try:
            # Convert and validate data types
            product_data = {
                'sku': str(row['sku']).strip(),
                'name': str(row['name']).strip(),
                'brand': str(row['brand']).strip(),
                'color': str(row['color']).strip() if 'color' in row and pd.notna(row['color']) else None,
                'size': str(row['size']).strip() if 'size' in row and pd.notna(row['size']) else None,
                'mrp': float(str(row['mrp']).replace('₹', '').replace(',', '').strip()),
                'price': float(str(row['price']).replace('₹', '').replace(',', '').strip()),
                'quantity': int(float(str(row['quantity']).strip()))
            }
            print(f"Processing row: {product_data}")
            
            # Validate through Pydantic model
            product = schemas.ProductBase(**product_data)
            
            # Check if product with same SKU exists
            existing_product = db.query(models.Product).filter(models.Product.sku == product_data['sku']).first()
            if existing_product:
                # Update existing product
                for key, value in product_data.items():
                    setattr(existing_product, key, value)
            else:
                # Create new product
                db_product = models.Product(**product_data)
                db.add(db_product)
            
            db.commit()
            stored += 1
            
        except ValueError as e:
            failed.append(f"Row {index + 2}: Invalid data format - {str(e)}")
            db.rollback()
        except IntegrityError as e:
            failed.append(f"Row {index + 2}: Database error - Duplicate SKU or invalid data")
            db.rollback()
        except Exception as e:
            failed.append(f"Row {index + 2}: {str(e)}")
            db.rollback()
    
    return {"stored": stored, "failed": failed}