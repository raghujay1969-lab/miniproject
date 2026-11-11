# Train Catering and Pre-Meal Ordering System

A mini-project web application built with **Python Flask, SQLite, HTML, CSS and JavaScript**.

## Features
- Passenger registration and login (passwords are hashed).
- Food menu with categories and prices.
- Shopping cart with quantity updates.
- Pre-meal ordering using train, PNR, coach/seat, delivery station and preferred delivery time.
- Order history and status tracking.
- Admin dashboard to add/disable menu items and update order statuses.
- SQLite database is created automatically on first run.

## Requirements
- Python 3.9 or later
- Internet connection is not required after Flask is installed.

## Run on Windows
1. Extract the ZIP file.
2. Open Command Prompt in the extracted `train_catering_app` folder.
3. Create a virtual environment (recommended):
   `python -m venv venv`
4. Activate it:
   `venv\Scripts\activate`
5. Install dependencies:
   `pip install -r requirements.txt`
6. Start the application:
   `python app.py`
7. Open `http://127.0.0.1:5000` in your browser.

## Run on macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Demo administrator account
- Email: `admin@trainmeal.demo`
- Password: `Admin@123`

Change the demo password and `SECRET_KEY` before any real deployment.

## Passenger workflow
1. Register and log in.
2. Select food items and add them to cart.
3. Open Cart and update quantities if required.
4. Proceed to Checkout and enter train journey details.
5. Place the order and view its status under My Orders.

## Admin workflow
1. Log in using the demo administrator account.
2. Open Admin.
3. Add food items or mark existing items unavailable/available.
4. Update order status as it moves through preparation and delivery.

## Database tables
- `users`: passenger and administrator accounts.
- `foods`: food menu, category, price and availability.
- `orders`: train journey, delivery details, total, status and timestamp.
- `order_items`: ordered food, quantity and unit price.

## Important project note
This is an academic demonstration. It does not connect to IRCTC, railway systems, live train locations, real PNR validation or a payment gateway. The demo uses Cash on Delivery as a placeholder payment method. Use fictional passenger and journey details while testing.
