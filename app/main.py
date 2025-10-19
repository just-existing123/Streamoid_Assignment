from fastapi import FastAPI, UploadFile, HTTPException, Query, Depends, Request, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
import os
from . import models, schemas, database
from .utils import process_csv

import pathlib

app = FastAPI(title="Product Catalog API")

# Configure templates and static files
base_dir = pathlib.Path(__file__).parent
templates = Jinja2Templates(directory=str(base_dir / "templates"))
static_dir = base_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"status": "ok"})

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
models.Base.metadata.create_all(bind=database.engine)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/debug/products")
async def debug_products(db: Session = Depends(get_db)):
    """Debug endpoint to check all products in database"""
    try:
        products = db.query(models.Product).all()
        result = [{
            "sku": p.sku,
            "name": p.name,
            "brand": p.brand,
            "color": p.color,
            "size": p.size,
            "mrp": p.mrp,
            "price": p.price,
            "quantity": p.quantity
        } for p in products]
        logger.info(f"Found {len(result)} products in database")
        return result
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request, 
    sku: str = Query(None),
    brand: str = Query(None),
    color: str = Query(None),
    size: str = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    message: str = Query(None),
    message_type: str = Query(None),
    db: Session = Depends(get_db)):
    try:
        query = db.query(models.Product)
        all_products = query.all()
        print(f"Total products in database: {len(all_products)}")
        for p in all_products:
            print(f"Product: SKU={p.sku}, Brand={p.brand}, Color={p.color}, Size={p.size}, Price={p.price}")
        filters = []
        try:
            if sku and sku.strip():
                sku = sku.strip()
                filters.append(models.Product.sku.ilike(f"%{sku}%"))
                print(f"Searching for SKU containing: {sku}")
            if brand and brand.strip():
                brand_search = brand.strip().replace(" ", "").lower()
                from sqlalchemy import func
                filters.append(func.lower(func.replace(models.Product.brand, ' ', '')).ilike(f"%{brand_search}%"))
                print(f"Searching for brand containing: {brand_search}")
            if color and color.strip():
                color_search = color.strip().replace(" ", "").lower()
                filters.append(func.lower(func.replace(models.Product.color, ' ', '')).ilike(f"%{color_search}%"))
                print(f"Searching for color containing: {color_search}")
            if size and size.strip():
                size_search = size.strip().replace(" ", "").lower()
                filters.append(func.lower(func.replace(models.Product.size, ' ', '')).ilike(f"%{size_search}%"))
                print(f"Searching for size containing: {size_search}")
            if min_price is not None:
                try:
                    min_price = float(min_price)
                    filters.append(models.Product.price >= min_price)
                    print(f"Searching for price >= {min_price}")
                except (ValueError, TypeError):
                    print("Invalid min_price value")
            if max_price is not None:
                try:
                    max_price = float(max_price)
                    filters.append(models.Product.price <= max_price)
                    print(f"Searching for price <= {max_price}")
                except (ValueError, TypeError):
                    print("Invalid max_price value")
        except Exception as filter_error:
            print(f"Error constructing filters: {filter_error}")
            import traceback
            print(traceback.format_exc())
            return HTMLResponse(content=f"<h2>Internal Server Error (filter construction)</h2><pre>{str(filter_error)}</pre>", status_code=500)
        if filters:
            try:
                query = query.filter(and_(*filters))
                print(f"SQL Query: {str(query)}")
                products = query.all()
                logger.info(f"Found {len(products)} products after applying {len(filters)} filters")
                for p in products:
                    logger.info(f"Match: SKU={p.sku}, Brand={p.brand}, Color={p.color}, Size={p.size}, Price={p.price}")
            except Exception as query_error:
                print(f"Error executing query: {query_error}")
                import traceback
                print(traceback.format_exc())
                return HTMLResponse(content=f"<h2>Internal Server Error (query execution)</h2><pre>{str(query_error)}</pre>", status_code=500)
        else:
            products = query.all()
            logger.info("No filters applied, showing all products")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "products": products,
                "message": message,
                "message_type": message_type,
                "search_params": {
                    "sku": sku or "",
                    "brand": brand or "",
                    "color": color or "",
                    "size": size or "",
                    "min_price": min_price or "",
                    "max_price": max_price or ""
                }
            }
        )
    except Exception as e:
        logger.error(f"Exception in home endpoint: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return HTMLResponse(content=f"<h2>Internal Server Error</h2><pre>{str(e)}</pre>", status_code=500)

@app.post("/upload")
async def upload_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        if not file.filename.endswith('.csv'):
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "message": "Only CSV files are allowed",
                    "message_type": "danger"
                }
            )
        result = await process_csv(file, db)
        return RedirectResponse(
            url=f"/?message=Successfully uploaded {result['stored']} products&message_type=success",
            status_code=302
        )
    except Exception as e:
        logger.error(f"Exception in upload_csv endpoint: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return HTMLResponse(content=f"<h2>Internal Server Error</h2><pre>{str(e)}</pre>", status_code=500)

@app.get("/products", response_model=List[schemas.Product])
def list_products(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/search", response_model=List[schemas.Product])
def search_products(
    sku: Optional[str] = None,
    brand: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)
    
    if sku:
        query = query.filter(models.Product.sku.ilike(f"%{sku}%"))
    if brand:
        query = query.filter(models.Product.brand.ilike(f"%{brand}%"))
    if color:
        query = query.filter(models.Product.color.ilike(f"%{color}%"))
    if size:
        query = query.filter(models.Product.size.ilike(f"%{size}%"))
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
        
    return query.all()
    query = db.query(models.Product)
    
    if brand:
        query = query.filter(models.Product.brand == brand)
    if color:
        query = query.filter(models.Product.color == color)
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
        
    return query.all()