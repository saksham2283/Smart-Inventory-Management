from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float)

    def __repr__(self):
        return f'<Product {self.name}>'

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'password123':
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Incorrect username or password!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Homepage
@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    products = Product.query.all()
    forecast_data = {}

    if os.path.exists('sales_data.csv'):
        df = pd.read_csv('sales_data.csv')
        for product in df['product_name'].unique():
            forecast_data[product] = df[df['product_name'] == product]['units_sold'].tail(7).sum()

    stock_status = []
    for product in products:
        predicted = forecast_data.get(product.name, 0)
        stock_status.append({
            'product': product.name,
            'current_stock': product.quantity,
            'predicted_demand': predicted,
            'alert': predicted > product.quantity
        })

    return render_template('home.html', stock_status=stock_status)

# Update stock manually
@app.route('/update_stock', methods=['POST'])
def update_stock():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    product_name = request.form['product_name']
    quantity = int(request.form['quantity'])
    product = Product.query.filter_by(name=product_name).first()

    if product:
        product.quantity = quantity
    else:
        product = Product(name=product_name, quantity=quantity)
        db.session.add(product)

    db.session.commit()
    flash('Stock updated successfully!', 'success')
    return redirect(url_for('home'))

# Upload sales CSV
@app.route('/upload_sales', methods=['GET', 'POST'])
def upload_sales():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['sales_csv']
        if file:
            df = pd.read_csv(file)

            for product_name in df['product_name'].unique():
                total_sold = df[df['product_name'] == product_name]['units_sold'].sum()
                product = Product.query.filter_by(name=product_name).first()
                if product:
                    product.quantity = max(product.quantity - total_sold, 0)
                else:
                    product = Product(name=product_name, quantity=0)
                    db.session.add(product)

            db.session.commit()
            df.to_csv('sales_data.csv', index=False)
            flash('Sales uploaded and stock updated!', 'success')
            return redirect(url_for('home'))

    return render_template('upload_sales.html')

# Upload stock Excel
@app.route('/upload_stock_excel', methods=['GET', 'POST'])
def upload_stock_excel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['stock_excel']
        if file:
            df = pd.read_excel(file)

            for _, row in df.iterrows():
                name = row['product_name']
                quantity = int(row['quantity'])
                category = row.get('category', '')
                price = float(row.get('price', 0.0))

                product = Product.query.filter_by(name=name).first()
                if not product:
                    product = Product(name=name, category=category, quantity=quantity, price=price)
                    db.session.add(product)
                else:
                    product.quantity = quantity
                    product.category = category
                    product.price = price

            db.session.commit()
            flash('Stock updated from Excel file!', 'success')
            return redirect(url_for('home'))

    return render_template('upload_stock_excel.html')

# Forecast graph viewer
@app.route('/forecast')
def show_forecasts():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    graphs = [f for f in os.listdir('static') if f.endswith('_forecast.png')]
    return render_template('forecast.html', graphs=graphs)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
