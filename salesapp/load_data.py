import pandas as pd
from .models import Product, SalesData


def load_csv(file_path):
    df = pd.read_csv(file_path)

    # Convert date column
    df['date'] = pd.to_datetime(df['date'])

    for _, row in df.iterrows():
        # Create or get product
        product, _ = Product.objects.get_or_create(
            product_id=row['product_id'],
            defaults={'department': row['department']}
        )

        # Insert sales data
        SalesData.objects.create(
            product=product,
            date=row['date'],
            size=row['size'],
            color=row['color'],
            daily_sales=int(row['daily_sales']),
            stock_level=int(row['stock_level']),
            season=row['Season']   
        )