import pandas as pd
from app import database, models

# Ensure tables exist
models.Base.metadata.create_all(bind=database.engine)

# Read CSV
df = pd.read_csv('sample_products.csv')

session = database.SessionLocal()
inserted = []
try:
    for index, row in df.iterrows():
        sku = str(row['sku']).strip()
        if not sku:
            continue
        product = session.query(models.Product).filter_by(sku=sku).first()
        data = dict(
            sku=sku,
            name=str(row.get('name','')).strip(),
            brand=str(row.get('brand','')).strip(),
            color=str(row.get('color','')).strip() if pd.notna(row.get('color')) else None,
            size=str(row.get('size','')).strip() if pd.notna(row.get('size')) else None,
            mrp=float(row.get('mrp') if pd.notna(row.get('mrp')) else 0),
            price=float(row.get('price') if pd.notna(row.get('price')) else 0),
            quantity=int(row.get('quantity') if pd.notna(row.get('quantity')) else 0)
        )
        if product:
            for k,v in data.items():
                setattr(product,k,v)
        else:
            product = models.Product(**data)
            session.add(product)
        session.commit()
        inserted.append(data)
finally:
    session.close()

print('Inserted rows:')
for r in inserted:
    print(r)

session = database.SessionLocal()
count = session.query(models.Product).count()
session.close()
print('Total products in DB:', count)
