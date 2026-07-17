"""
Lemon Button Cafe - Ordering System
Flask + SQLite backend.

Run:      python app.py
Customer: http://localhost:5000/
Admin:    http://localhost:5000/admin
"""

from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import sqlite3
import os
import json
from datetime import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# On Render, /var/data is a persistent disk mount (if attached).
# Falls back to local file otherwise.
DB_DIR  = os.environ.get("DB_DIR", APP_DIR)
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "orders.db")

app = Flask(__name__)


# ------------------------------------------------------------
# Database helpers
# ------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT    NOT NULL,
            room_number   TEXT,
            phone         TEXT,
            notes         TEXT,
            items_json    TEXT    NOT NULL,
            item_count    INTEGER NOT NULL,
            created_at    TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


# ------------------------------------------------------------
# Menu data (extracted from Lemon Button Cafe 2026 menu)
# ------------------------------------------------------------
MENU = [
    {
        "category": "Tapas",
        "items": [
            {"name": "Prawn Chili Olio", "desc": "Prawn in garlic, chili and olive oil, 3 slices of toasted crispy garlic butter baguette."},
            {"name": "Chef's Special Beef Hor Fun", "desc": "Wok hei flat rice noodles in light oyster sauce with beef slice, vegetables, egg sauce."},
            {"name": "Classic Mushroom", "desc": "Served with toasted garlic bread (2 pcs)."},
            {"name": "Deep Fried Dumpling", "desc": "Chicken dumpling served with Thai chili dipping sauce."},
            {"name": "Panipuri", "desc": "Crispy puris (6 pcs) with tangy tamarind sauce, flavourful potato mix, mixed salad."},
        ],
    },
    {
        "category": "Pot & Wok",
        "items": [
            {"name": "Lemon Button Chicken Curry", "desc": "Cooked with potatoes and tomato. Served with steamed white rice."},
        ],
    },
    {
        "category": "Local Favourite",
        "items": [
            {"name": "Singapore Fried Bee Hoon", "desc": "Meehoon stir-fried with chicken, prawn and egg."},
            {"name": "Lemon Button Mee Goreng Mamak", "desc": "Stir-fried yellow noodles with prawn, chicken, fish cake and beancurd."},
            {"name": "Lemon Button Signature Fried Rice", "desc": "White rice fried with homemade spicy prawn paste, chicken, prawn, fried egg and keropok."},
            {"name": "Wok Fried Koay Teow", "desc": "Flat rice noodles stir-fried with soy sauce, prawn, chicken, fish cake, vegetables and egg."},
            {"name": "Cantonese Fried Rice", "desc": "White rice fried with chicken, prawn, vegetables, fried egg, keropok + chicken wing + steamed rice."},
        ],
    },
    {
        "category": "Sharing Delight",
        "items": [
            {"name": "House Special Wings", "desc": "Chicken wings glazed with honey and special homemade seasoning."},
            {"name": "Cameron Farmer's Market Feast", "desc": "Stir-fried mixed vegetables."},
            {"name": "Homemade Soup", "desc": "Served with 1 pc garlic bread."},
            {"name": "Cajun Potato Wedges", "desc": "Wedges served with cajun mayo."},
            {"name": "Potato Fries", "desc": "Served with mayonnaise dip."},
        ],
    },
    {
        "category": "Salad",
        "items": [
            {"name": "Cameron Special Salad", "desc": "Orange, strawberry, green salad with citrus vinaigrette."},
            {"name": "Cream of Pumpkin", "desc": "Roast pumpkin with oregano, onion, and cream."},
            {"name": "Classic Greek Salad", "desc": "Romaine, tomatoes, cucumbers, olives, capsicum, onions, feta cheese, zesty house dressing."},
            {"name": "Nicoise Salad", "desc": "Romaine, tomatoes, cucumber, olives, boiled potato, boiled egg, french bean and tuna chunk with dressing."},
        ],
    },
    {
        "category": "Kiddo's Menu",
        "items": [
            {"name": "Kiddo Chicken Nugget with Sausage", "desc": "3 pcs nugget, 2 pcs cocktail sausage, sauté mixed vege, cut fruits."},
            {"name": "Kiddo Fish and Chips", "desc": "Crispy battered fried fish with golden fries, tartar sauce, cut fruits."},
            {"name": "Kiddo Spaghetti Bolognese", "desc": "Ground beef in Italian tomato sauce, parmesan, sauté mixed vege, cut fruits."},
            {"name": "Kiddo Meatballs and Mash", "desc": "5 pcs homemade chicken meatballs, mash potato, brown sauce, cut fruits."},
            {"name": "Kiddo Mac and Cheese", "desc": "Mac and cheese, sauté mixed vege, cut fruits."},
        ],
    },
    {
        "category": "Warisan Flavours",
        "items": [
            {"name": "Village-Style Ayam Penyet", "desc": "Smashed fried chicken, white rice, ulam-ulaman, eggplant with sambal hijau, keropok, clear chicken soup."},
            {"name": "Briyani Rice with Ayam Masak Merah", "desc": "Spiced briyani rice, chicken in spicy tomato gravy, pickled vege, papadom, eggplant sambal hijau."},
            {"name": "Briyani Rice with Beef Peratal", "desc": "Spiced briyani rice with slow-cooked beef peratal, pickled vege, papadom, eggplant sambal hijau."},
        ],
    },
    {
        "category": "Slurp & Savour",
        "items": [
            {"name": "Udon Noodle Soup", "desc": "Udon in dashi broth with chicken thigh, white tofu, half-boiled egg, nori, wakame, sesame, spring onions."},
            {"name": "Classic Beef Broth Noodles", "desc": "Vermicelli or yellow noodles with beef tenderloin, beef balls in herb-infused broth with sambal kicap."},
            {"name": "Creamy Thai Tomyum Pasta", "desc": "Spaghetti with prawns and mussels in creamy Tom Yum sauce."},
            {"name": "Sarawak Laksa", "desc": "Vermicelli with prawns, shredded chicken and egg omelette in authentic Sarawak laksa gravy."},
        ],
    },
    {
        "category": "Western Favourites — Mains",
        "items": [
            {"name": "Beef Steak", "desc": "Sirloin steak (200 g), sautéed vegetables, mashed potatoes, black pepper sauce."},
            {"name": "Classic Fish & Chips", "desc": "Crispy battered fried fish, golden fries, coleslaw, lemon slice, tartar sauce."},
            {"name": "Grilled Chicken Chop", "desc": "Butter mixed vegetables, mashed potatoes, black pepper sauce."},
            {"name": "Classic Chicken Roulade", "desc": "Chicken breast, cheddar, spinach, caramelized onion, mixed vege, sautéed potatoes."},
            {"name": "Grill Lamb Rack", "desc": "Lamb rack (250 g), butter mixed vegetables, mashed potatoes, mint sauce."},
        ],
    },
    {
        "category": "Pasta & Pizza",
        "items": [
            {"name": "Spaghetti Beef Bolognese", "desc": "Ground beef in Italian tomato sauce, grated parmesan cheese."},
            {"name": "Spaghetti Prawn Marinara", "desc": "Prawns in Italian marinara sauce, vegetables, oregano."},
            {"name": "Spaghetti Carbonara", "desc": "Fresh mushroom, chicken ham."},
            {"name": "Fisherman Pasta", "desc": "Grilled salmon with prawns and spaghetti aglio olio."},
            {"name": "Tangy Chicken Pizza", "desc": "Sliced chicken, chicken ham, onion, capsicum, pineapple, mozzarella."},
            {"name": "Lemon Button Special Pizza", "desc": "Capsicum, onion, fresh mushroom, mozzarella cheese."},
        ],
    },
    {
        "category": "Burgers",
        "items": [
            {"name": "Lemon Button Beef Burger", "desc": "Beef patty, coleslaw, potato fries."},
            {"name": "Lemon Button Chicken Burger", "desc": "Marinated chicken chop, cheddar cheese, fried egg, coleslaw, potato fries."},
        ],
    },
    {
        "category": "Desserts",
        "items": [
            {"name": "Ice Cream", "desc": "Choice of vanilla, strawberry, chocolate."},
            {"name": "Fresh Fruits Platter", "desc": "Assorted fresh seasonal fruits."},
            {"name": "Chocolate Brownies", "desc": "Chocolate fudge brownie served with vanilla ice cream."},
            {"name": "Homemade Scones (2 pcs)", "desc": "Homemade strawberry jam, butter, fresh whipped cream."},
            {"name": "Cake of the Day", "desc": "Chef's daily selection."},
            {"name": "Waffle with Cream and Strawberry Coulis", "desc": "Classic waffle, homemade strawberry coulis with cream."},
            {"name": "Sago Gula Melaka", "desc": "Sago, gula melaka, coconut milk."},
        ],
    },
    {
        "category": "Signature / Platters",
        "items": [
            {"name": "Local Delight High Tea", "desc": "2 freshly baked scones with strawberry jam, butter, whipped cream and a cup of tea."},
            {"name": "Steamboat", "desc": "Fresh vegetables, chicken, calamari, prawns, fishballs, crab sticks, 2 noodle types, eggs & fried rice. Choice of Chicken or Tomyam soup."},
        ],
    },
    {
        "category": "Tea",
        "items": [
            {"name": "Honey Flower Tea — Jasmine", "desc": "Honey flower tea."},
            {"name": "Honey Flower Tea — Lavender", "desc": "Honey flower tea."},
            {"name": "Honey Flower Tea — Roselle", "desc": "Honey flower tea."},
            {"name": "Honey Flower Tea — Rose", "desc": "Honey flower tea."},
            {"name": "Honey Flower Tea — Butterfly Pea", "desc": "Honey flower tea."},
            {"name": "Mix Flower Tea", "desc": "Blend of flower teas."},
            {"name": "English Breakfast", "desc": "Specialty tea."},
            {"name": "Earl Grey", "desc": "Specialty tea."},
            {"name": "Green Tea", "desc": "Specialty tea."},
            {"name": "Chamomile", "desc": "Specialty tea."},
            {"name": "Strawberry Tea", "desc": "Specialty tea."},
            {"name": "Lychee Tea", "desc": "Specialty tea."},
            {"name": "Masala Ginger Lemon", "desc": "Local tea."},
            {"name": "Honey Lemon", "desc": "Local tea."},
            {"name": "Teh Tarik", "desc": "Local tea."},
            {"name": "Ice Lemon Tea", "desc": "Local tea."},
        ],
    },
    {
        "category": "Coffee & Chocolate",
        "items": [
            {"name": "Single Espresso", "desc": ""},
            {"name": "Double Espresso", "desc": ""},
            {"name": "Long Black", "desc": ""},
            {"name": "Flat White", "desc": ""},
            {"name": "Cappuccino", "desc": ""},
            {"name": "Caffe Latte", "desc": ""},
            {"name": "Hot Chocolate", "desc": ""},
            {"name": "Nescafe", "desc": ""},
            {"name": "Milo", "desc": ""},
            {"name": "Coffee with Milk", "desc": ""},
            {"name": "Kopi 'O'", "desc": ""},
            {"name": "Chai Latte", "desc": ""},
        ],
    },
    {
        "category": "Fresh Juices",
        "items": [
            {"name": "Carrot Juice", "desc": "Freshly pressed."},
            {"name": "Orange Juice", "desc": "Freshly pressed."},
            {"name": "Watermelon Juice", "desc": "Freshly pressed."},
            {"name": "Mixed Juice (2 Varieties)", "desc": "Please state preference in notes."},
        ],
    },
    {
        "category": "Milkshakes",
        "items": [
            {"name": "Vanilla Milkshake", "desc": ""},
            {"name": "Chocolate Milkshake", "desc": ""},
            {"name": "Strawberry Milkshake", "desc": ""},
            {"name": "Coffee Milkshake", "desc": ""},
            {"name": "Oreo Milkshake", "desc": ""},
        ],
    },
    {
        "category": "Mocktails",
        "items": [
            {"name": "Shirley Temple", "desc": ""},
            {"name": "Fruit Punch", "desc": ""},
            {"name": "Virgin Mojito", "desc": ""},
            {"name": "Orange Mojito", "desc": ""},
            {"name": "Cranberry Mojito", "desc": ""},
        ],
    },
    {
        "category": "Refreshers",
        "items": [
            {"name": "Lychee Mint", "desc": ""},
            {"name": "Ribena Longan", "desc": ""},
            {"name": "Bora Bora", "desc": ""},
            {"name": "Strawberry Delight", "desc": ""},
            {"name": "Mango Tango Lagoon", "desc": ""},
            {"name": "Lemon Button's Lemonade", "desc": ""},
            {"name": "Mango Paplovo", "desc": ""},
        ],
    },
    {
        "category": "Other Beverages",
        "items": [
            {"name": "Mineral Water 500 ml", "desc": "Still mineral water."},
            {"name": "Sparkling Water", "desc": ""},
            {"name": "Coke", "desc": ""},
            {"name": "Coke Zero", "desc": ""},
            {"name": "Sprite", "desc": ""},
            {"name": "A&W Float", "desc": ""},
        ],
    },
]


# ------------------------------------------------------------
# Templates
# ------------------------------------------------------------
CUSTOMER_HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Lemon Button Cafe — Order Menu</title>
<style>
 :root{
   --lemon:#f7d94c; --lemon-dk:#d4b400; --ink:#2b2b2b;
   --paper:#fffdf5; --line:#efe6b8; --accent:#3f7d43;
 }
 *{box-sizing:border-box}
 body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
      background:var(--paper);color:var(--ink);line-height:1.5}
 header{background:linear-gradient(135deg,var(--lemon),var(--lemon-dk));
        padding:28px 20px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.08)}
 header h1{margin:0;font-size:2rem;letter-spacing:1px}
 header p{margin:6px 0 0;font-size:.95rem;opacity:.8}
 .wrap{max-width:900px;margin:0 auto;padding:24px 18px 120px}
 .card{background:#fff;border:1px solid var(--line);border-radius:12px;
       padding:20px;margin-bottom:22px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
 .card h2{margin:0 0 10px;font-size:1.15rem;color:var(--accent);
         border-bottom:2px dashed var(--lemon);padding-bottom:6px}
 label.field{display:block;margin-bottom:12px;font-weight:600;font-size:.9rem}
 label.field input,label.field textarea{width:100%;padding:10px 12px;font-size:1rem;
   border:1px solid #ddd;border-radius:8px;font-family:inherit;margin-top:4px}
 label.field textarea{min-height:70px;resize:vertical}
 .cat{margin-bottom:22px}
 .cat h3{margin:0 0 8px;font-size:1.05rem;color:var(--ink);
         background:var(--lemon);padding:8px 12px;border-radius:8px;display:inline-block}
 .item{display:flex;align-items:flex-start;gap:10px;padding:10px 6px;
       border-bottom:1px dotted #eadb6d}
 .item:last-child{border-bottom:none}
 .item input[type=checkbox]{margin-top:4px;transform:scale(1.25);accent-color:var(--accent);cursor:pointer}
 .item label{flex:1;cursor:pointer}
 .item .name{font-weight:600}
 .item .desc{font-size:.85rem;color:#666;margin-top:2px}
 .qty{width:56px;padding:4px 6px;border:1px solid #ccc;border-radius:6px;
      font-size:.9rem;text-align:center}
 .submit-bar{position:fixed;bottom:0;left:0;right:0;background:#fff;
             border-top:1px solid var(--line);padding:12px 18px;
             display:flex;align-items:center;gap:12px;justify-content:space-between;
             box-shadow:0 -2px 8px rgba(0,0,0,.06)}
 .count{font-weight:600}
 button.primary{background:var(--accent);color:#fff;border:0;padding:12px 24px;
                border-radius:10px;font-size:1rem;font-weight:600;cursor:pointer}
 button.primary:disabled{opacity:.5;cursor:not-allowed}
 .banner{background:#e7f6e8;border:1px solid #b7dfba;color:#245c28;
         padding:14px;border-radius:10px;margin-bottom:18px;display:none}
</style>
</head>
<body>
<header>
  <h1>🍋 Lemon Button Cafe</h1>
  <p>Hotel De'La Ferns • Cameron Highlands</p>
</header>

<form id="orderForm" class="wrap" onsubmit="return submitOrder(event)">
  <div id="successBanner" class="banner"></div>

  <div class="card">
    <h2>Your Details</h2>
    <label class="field">Name *
      <input type="text" name="customer_name" required maxlength="80" placeholder="Full name" />
    </label>
    <label class="field">Allergies
      <textarea name="notes" placeholder="Allergies, no peanuts, no dairy, etc."></textarea>
    </label>
  </div>

  <div class="card">
    <h2>Choose Your Meals</h2>
    <p style="margin-top:0;font-size:.9rem;color:#666">Tick the items you would like to order. Adjust quantity if needed.</p>
    {% for cat in menu %}
      <div class="cat">
        <h3>{{ cat.category }}</h3>
        {% for item in cat['items'] %}
          <div class="item">
            <input type="checkbox" id="chk_{{ loop.index0 }}_{{ loop.index }}_{{ cat.category|replace(' ','_') }}"
                   class="menu-check"
                   data-category="{{ cat.category }}"
                   data-name="{{ item.name }}"
                   onchange="updateCount()"/>
            <label for="chk_{{ loop.index0 }}_{{ loop.index }}_{{ cat.category|replace(' ','_') }}">
              <div class="name">{{ item.name }}</div>
              {% if item.desc %}<div class="desc">{{ item.desc }}</div>{% endif %}
            </label>
            <input type="number" class="qty" min="1" max="20" value="1" title="Quantity" />
          </div>
        {% endfor %}
      </div>
    {% endfor %}
  </div>

  <div class="submit-bar">
    <span class="count">Selected: <span id="cnt">0</span> item(s)</span>
    <button type="submit" class="primary" id="submitBtn" disabled>Place Order</button>
  </div>
</form>

<script>
function updateCount(){
  const n = document.querySelectorAll('.menu-check:checked').length;
  document.getElementById('cnt').textContent = n;
  document.getElementById('submitBtn').disabled = (n === 0);
}

async function submitOrder(ev){
  ev.preventDefault();
  const form = ev.target;
  const items = [];
  document.querySelectorAll('.menu-check:checked').forEach(chk=>{
    const qty = chk.parentElement.querySelector('.qty').value || 1;
    items.push({
      category: chk.dataset.category,
      name: chk.dataset.name,
      quantity: parseInt(qty,10)
    });
  });
  if(items.length === 0){ alert('Please select at least one item.'); return false; }

  const payload = {
    customer_name: form.customer_name.value.trim(),
    notes:         form.notes.value.trim(),
    items: items
  };

  const btn = document.getElementById('submitBtn');
  btn.disabled = true; btn.textContent = 'Placing...';

  try{
    const res = await fetch('/api/orders',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || 'Failed');

    const banner = document.getElementById('successBanner');
    banner.style.display = 'block';
    banner.innerHTML = '✅ Thank you, <b>' + payload.customer_name +
      '</b>! Your order #' + data.order_id + ' with ' + items.length +
      ' item(s) has been received.';
    form.reset();
    document.querySelectorAll('.menu-check').forEach(c=>c.checked=false);
    updateCount();
    window.scrollTo({top:0,behavior:'smooth'});
  }catch(err){
    alert('Error placing order: ' + err.message);
  }finally{
    btn.textContent = 'Place Order';
    updateCount();
  }
  return false;
}
</script>
</body>
</html>
"""


ADMIN_HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Admin — Lemon Button Cafe Orders</title>
<style>
 body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
      background:#f5f5f5;color:#222}
 header{background:#2b2b2b;color:#f7d94c;padding:18px 22px;
        display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
 header h1{margin:0;font-size:1.25rem}
 header a{color:#f7d94c;text-decoration:none;font-size:.9rem;margin-left:14px}
 .wrap{max-width:1200px;margin:0 auto;padding:20px}
 .stats{display:flex;gap:14px;margin-bottom:16px;flex-wrap:wrap}
 .stat{background:#fff;padding:14px 18px;border-radius:10px;
       box-shadow:0 1px 3px rgba(0,0,0,.06);min-width:130px}
 .stat .lbl{font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:1px}
 .stat .val{font-size:1.6rem;font-weight:700;color:#3f7d43;margin-top:2px}
 table{width:100%;background:#fff;border-collapse:collapse;
       border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06)}
 th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #eee;font-size:.9rem;vertical-align:top}
 th{background:#f7d94c;color:#2b2b2b;font-weight:700;font-size:.8rem;text-transform:uppercase;letter-spacing:.5px}
 tr:hover{background:#fffdf0}
 .items{margin:0;padding-left:18px}
 .items li{margin:2px 0}
 .empty{text-align:center;padding:40px;color:#888}
 .btns{margin:10px 0 18px;display:flex;gap:10px;flex-wrap:wrap}
 .btn{background:#3f7d43;color:#fff;padding:8px 14px;border-radius:8px;
      text-decoration:none;font-size:.85rem;font-weight:600;border:0;cursor:pointer}
 .btn.warn{background:#c62828}
 .badge{display:inline-block;background:#3f7d43;color:#fff;padding:2px 8px;
        border-radius:10px;font-size:.75rem;font-weight:600}
</style>
</head>
<body>
<header>
  <h1>🍋 Lemon Button Cafe — Orders Dashboard</h1>
  <div>
    <a href="/">← Customer Menu</a>
    <a href="/api/orders.json" target="_blank">JSON Export</a>
    <a href="/api/orders.csv">CSV Export</a>
  </div>
</header>

<div class="wrap">
  <div class="stats">
    <div class="stat"><div class="lbl">Total Orders</div><div class="val">{{ total_orders }}</div></div>
    <div class="stat"><div class="lbl">Total Items Ordered</div><div class="val">{{ total_items }}</div></div>
    <div class="stat"><div class="lbl">Unique Customers</div><div class="val">{{ unique_customers }}</div></div>
    <div class="stat"><div class="lbl">Today's Orders</div><div class="val">{{ today_orders }}</div></div>
  </div>

  {% if orders %}
  <table>
    <thead>
      <tr>
        <th>#</th><th>Time</th><th>Customer</th>
        <th>Items Ordered</th><th>Qty</th><th>Allergies</th>
      </tr>
    </thead>
    <tbody>
      {% for o in orders %}
      <tr>
        <td><b>#{{ o.id }}</b></td>
        <td>{{ o.created_at }}</td>
        <td>{{ o.customer_name }}</td>
        <td>
          <ul class="items">
            {% for it in o.items %}
              <li><b>{{ it.name }}</b>{% if it.quantity and it.quantity > 1 %} × {{ it.quantity }}{% endif %}
                  <span style="color:#888;font-size:.8rem">({{ it.category }})</span></li>
            {% endfor %}
          </ul>
        </td>
        <td><span class="badge">{{ o.item_count }}</span></td>
        <td style="max-width:200px">{{ o.notes or '' }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
    <div class="empty">No orders yet. Waiting for customers…</div>
  {% endif %}
</div>
</body>
</html>
"""


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.route("/")
def home():
    return render_template_string(CUSTOMER_HTML, menu=MENU)


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("customer_name") or "").strip()
    items = data.get("items") or []
    if not name:
        return jsonify({"error": "Customer name is required."}), 400
    if not items:
        return jsonify({"error": "At least one item is required."}), 400

    clean_items = []
    for it in items:
        clean_items.append({
            "category": str(it.get("category", ""))[:80],
            "name":     str(it.get("name", ""))[:120],
            "quantity": max(1, min(20, int(it.get("quantity") or 1))),
        })

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO orders(customer_name, room_number, phone, notes,
                              items_json, item_count, created_at)
           VALUES(?,?,?,?,?,?,?)""",
        (
            name,
            (data.get("room_number") or "").strip()[:40],
            (data.get("phone") or "").strip()[:40],
            (data.get("notes") or "").strip()[:500],
            json.dumps(clean_items, ensure_ascii=False),
            sum(i["quantity"] for i in clean_items),
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        ),
    )
    conn.commit()
    order_id = cur.lastrowid
    conn.close()
    return jsonify({"ok": True, "order_id": order_id})


@app.route("/admin")
def admin():
    conn = get_db()
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()

    orders = []
    for r in rows:
        orders.append({
            "id": r["id"],
            "customer_name": r["customer_name"],
            "room_number": r["room_number"],
            "phone": r["phone"],
            "notes": r["notes"],
            "item_count": r["item_count"],
            "created_at": r["created_at"],
            "items": json.loads(r["items_json"]),
        })

    today = datetime.utcnow().strftime("%Y-%m-%d")
    stats = {
        "total_orders": len(orders),
        "total_items":  sum(o["item_count"] for o in orders),
        "unique_customers": len({o["customer_name"].lower() for o in orders}),
        "today_orders": sum(1 for o in orders if o["created_at"].startswith(today)),
    }
    return render_template_string(ADMIN_HTML, orders=orders, **stats)


@app.route("/api/orders.json")
def orders_json():
    conn = get_db()
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([{
        "id": r["id"],
        "customer_name": r["customer_name"],
        "room_number": r["room_number"],
        "phone": r["phone"],
        "notes": r["notes"],
        "item_count": r["item_count"],
        "created_at": r["created_at"],
        "items": json.loads(r["items_json"]),
    } for r in rows])


@app.route("/api/orders.csv")
def orders_csv():
    import csv, io
    conn = get_db()
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Order ID","Time","Customer","Item Count","Items","Allergies"])
    for r in rows:
        items = json.loads(r["items_json"])
        items_str = "; ".join(f"{i['name']} x{i['quantity']} ({i['category']})" for i in items)
        w.writerow([r["id"], r["created_at"], r["customer_name"],
                    r["item_count"], items_str, r["notes"] or ""])
    from flask import Response
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment; filename=lemon_button_orders.csv"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Lemon Button Cafe running:")
    print(f"  Customer menu : http://localhost:{port}/")
    print(f"  Admin view    : http://localhost:{port}/admin")
    app.run(host="0.0.0.0", port=port, debug=False)
