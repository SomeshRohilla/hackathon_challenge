import pandas as pd
from prophet import Prophet
from collections import defaultdict

from .models import SalesData


def generate_forecast(days=7, product=None):

    days = int(days)

    # 🔥 FETCH DATA
    if product:
        data = SalesData.objects.filter(product=product).values(
            'date', 'daily_sales', 'size', 'stock_level'
        )
    else:
        data = SalesData.objects.all().values(
            'date', 'daily_sales', 'size', 'stock_level'
        )

    df = pd.DataFrame(data)

    if df.empty or len(df) < 2:
        return {"forecast": []}

    df['date'] = pd.to_datetime(df['date'])

    # 🔥 FORCE ALL SIZES (IMPORTANT FIX)
    sizes = ['Small', 'Medium', 'Large']

    all_forecasts = []

    # 🔥 TRAIN MODEL PER SIZE
    for size in sizes:

        size_df = df[df['size'] == size][['date', 'daily_sales']]

        # ✅ FIX: fallback if not enough data
        if len(size_df) < 2:
            last_value = size_df['daily_sales'].iloc[-1] if not size_df.empty else 0

            future_dates = pd.date_range(
                    start=df['date'].max() + pd.Timedelta(days=1),
                    periods=days
                )
            forecast = pd.DataFrame({
                'ds': future_dates,
                'yhat': [last_value] * len(future_dates),
                'yhat_lower': [last_value * 0.8] * len(future_dates),
                'yhat_upper': [last_value * 1.2] * len(future_dates),
                'size': size
            })

            all_forecasts.append(forecast)
            continue

        size_df.columns = ['ds', 'y']

        model = Prophet()
        model.fit(size_df)

        future = model.make_future_dataframe(periods=days)
        forecast = model.predict(future)
        forecast = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(days)
        forecast['size'] = size

        all_forecasts.append(forecast)

    # 🔥 COMBINE ALL SIZES
    combined = pd.concat(all_forecasts)

    # 🔥 GET LATEST STOCK PER SIZE
    stock_tracker = {}

    for size in sizes:
        size_data = df[df['size'] == size]

        if not size_data.empty:
            latest_stock = size_data.sort_values('date').iloc[-1]['stock_level']
        else:
            latest_stock = 0

        stock_tracker[size] = int(latest_stock)

    # 🔥 BUILD FINAL OUTPUT
    grouped = defaultdict(dict)

    for _, row in combined.iterrows():

        date = str(row['ds'].date())
        size = row['size']

        predicted = max(0, int(row['yhat']))

        stock_tracker[size] -= predicted

        grouped[date][size] = {
            "predicted_sales": predicted,
            "min_sales": int(row['yhat_lower']),
            "max_sales": int(row['yhat_upper']),
            "remaining_stock": stock_tracker[size]
        }

        # 🔥 OPTIONAL ALERT
        if stock_tracker[size] < 50:
            grouped[date][size]["alert"] = "Low Stock"

    # 🔥 ENSURE ALL SIZES ALWAYS PRESENT
    for date in grouped:
        for size in sizes:
            if size not in grouped[date]:
                grouped[date][size] = {
                    "predicted_sales": 0,
                    "min_sales": 0,
                    "max_sales": 0,
                    "remaining_stock": stock_tracker.get(size, 0)
                }

    # 🔥 FINAL JSON
    final_output = {
        "forecast": [
            {
                "date": date,
                "mugs": grouped[date]
            }
            for date in sorted(grouped.keys())
        ]
    }

    return final_output