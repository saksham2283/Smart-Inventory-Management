import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import os

# Read CSV
df = pd.read_csv('sales_data.csv')

# Make sure static folder exists
os.makedirs("static", exist_ok=True)

# Get all unique products
product_names = df['product_name'].unique()

for product in product_names:
    print(f"Forecasting for: {product}")
    product_df = df[df['product_name'] == product][['date', 'units_sold']]
    product_df = product_df.rename(columns={'date': 'ds', 'units_sold': 'y'})

    model = Prophet(daily_seasonality=True)
    model.fit(product_df)

    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)

    fig = model.plot(forecast)
    plt.title(f"{product} Sales Forecast")
    plt.xlabel("Date")
    plt.ylabel("Predicted Units Sold")

    file_path = f"static/{product}_forecast.png"
    fig.savefig(file_path)  # ✅ Saves the graph image
    plt.close(fig)          # ✅ Important! Prevents reuse of old plots
