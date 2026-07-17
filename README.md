# 🍋 Lemon Button Cafe — Ordering System

A simple ordering website with a private admin dashboard.

## What's inside
- `app.py`         — Flask app (customer form + admin view + SQLite database)
- `orders.db`      — auto-created SQLite database (stores every order)
- `requirements.txt`

## Run it
```
pip install -r requirements.txt
python app.py
```

Then open:
- **Customer menu**  → http://localhost:5000/
- **Admin dashboard** → http://localhost:5000/admin
- **JSON export**    → http://localhost:5000/api/orders.json
- **CSV export**     → http://localhost:5000/api/orders.csv

## Features
- Full 2026 menu (no prices shown to customer)
- Customer enters Name, Room, Phone, Notes
- Ticks the items they want + quantity
- Every order stored in `orders.db` (SQLite)
- Admin dashboard shows all orders, totals, today's count
- One-click CSV download for record keeping
