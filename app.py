from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json

app = Flask(__name__)
app.secret_key = 'bizapp-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bizapp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── Models ───────────────────────────────────────────────
class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    name     = db.Column(db.String(80), nullable=False)
    plan     = db.Column(db.String(20), default='free')  # free / premium
    created  = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    user_email   = db.Column(db.String(120))
    invoice_no   = db.Column(db.String(50))
    client_name  = db.Column(db.String(100))
    client_email = db.Column(db.String(120))
    items        = db.Column(db.Text)   # JSON
    total        = db.Column(db.Float)
    status       = db.Column(db.String(20), default='unpaid')
    date         = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120))
    title      = db.Column(db.String(100))
    amount     = db.Column(db.Float)
    category   = db.Column(db.String(50))
    date       = db.Column(db.DateTime, default=datetime.utcnow)

class Inventory(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120))
    name       = db.Column(db.String(100))
    quantity   = db.Column(db.Integer)
    price      = db.Column(db.Float)
    category   = db.Column(db.String(50))
    low_stock  = db.Column(db.Integer, default=5)

# ─── Helpers ──────────────────────────────────────────────
def get_user():
    return session.get('user')

def is_premium():
    user = get_user()
    return user and user.get('plan') == 'premium'

# ─── Routes ───────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', user=get_user())

@app.route('/login', methods=['POST'])
def login():
    data  = request.json
    email = data.get('email', '').strip()
    name  = data.get('name', '').strip()
    if not email or not name:
        return jsonify({'error': 'Email aur naam daalen!'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, name=name)
        db.session.add(user)
        db.session.commit()
    session['user'] = {'email': user.email, 'name': user.name, 'plan': user.plan}
    return jsonify({'success': True, 'user': session['user']})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/upgrade', methods=['POST'])
def upgrade():
    user = get_user()
    if not user:
        return jsonify({'error': 'Login karein!'}), 401
    u = User.query.filter_by(email=user['email']).first()
    u.plan = 'premium'
    db.session.commit()
    session['user']['plan'] = 'premium'
    return jsonify({'success': True})

# ── Invoice ──
@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    user = get_user()
    if not user: return jsonify({'error': 'Login karein!'}), 401
    invoices = Invoice.query.filter_by(user_email=user['email']).order_by(Invoice.date.desc()).all()
    if not is_premium() and len(invoices) >= 3:
        invoices = invoices[:3]
    result = []
    for inv in invoices:
        result.append({
            'id': inv.id, 'invoice_no': inv.invoice_no,
            'client_name': inv.client_name, 'total': inv.total,
            'status': inv.status, 'date': inv.date.strftime('%Y-%m-%d')
        })
    return jsonify(result)

@app.route('/api/invoices', methods=['POST'])
def create_invoice():
    user = get_user()
    if not user: return jsonify({'error': 'Login karein!'}), 401
    # Free plan limit
    count = Invoice.query.filter_by(user_email=user['email']).count()
    if not is_premium() and count >= 3:
        return jsonify({'error': 'FREE_LIMIT', 'message': 'Free plan mein sirf 3 invoices! Premium len.'}), 403
    data = request.json
    inv = Invoice(
        user_email=user['email'],
        invoice_no=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        client_name=data['client_name'],
        client_email=data.get('client_email', ''),
        items=json.dumps(data['items']),
        total=data['total'],
        status='unpaid'
    )
    db.session.add(inv)
    db.session.commit()
    return jsonify({'success': True, 'id': inv.id, 'invoice_no': inv.invoice_no})

@app.route('/api/invoices/<int:inv_id>/status', methods=['POST'])
def update_invoice_status(inv_id):
    inv = Invoice.query.get(inv_id)
    if inv:
        inv.status = request.json.get('status', 'unpaid')
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/invoices/<int:inv_id>', methods=['DELETE'])
def delete_invoice(inv_id):
    inv = Invoice.query.get(inv_id)
    if inv:
        db.session.delete(inv)
        db.session.commit()
    return jsonify({'success': True})

# ── Expense ──
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    user = get_user()
    if not user: return jsonify({'error': 'Login karein!'}), 401
    expenses = Expense.query.filter_by(user_email=user['email']).order_by(Expense.date.desc()).all()
    if not is_premium() and len(expenses) >= 10:
        expenses = expenses[:10]
    return jsonify([{
        'id': e.id, 'title': e.title, 'amount': e.amount,
        'category': e.category, 'date': e.date.strftime('%Y-%m-%d')
    } for e in expenses])

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    user = get_user()
    if not user: return jsonify({'error': 'Login karein!'}), 401
    count = Expense.query.filter_by(user_email=user['email']).count()
    if not is_premium() and count >= 10:
        return jsonify({'error': 'FREE_LIMIT', 'message': 'Free plan mein sirf 10 expenses! Premium len.'}), 403
    data = request.json
    exp = Expense(user_email=user['email'], title=data['title'],
                  amount=data['amount'], category=data['category'])
    db.session.add(exp)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/expenses/<int:exp_id>', methods=['DELETE'])
def delete_expense(exp_id):
    exp = Expense.query.get(exp_id)
    if exp:
        db.session.delete(exp)
        db.session.commit()
    return jsonify({'success': True})

# ── Inventory ──
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    user = get_user()
    if not user: return jsonify({'error': 'Login karein!'}), 401
    items = Inventory.query.filter_by(user_email=user['email']).all()
    if not is_premium() and len(items) >= 10:
        items = items[:10]
    return jsonify([{
        'id': i.id, 'name': i.name, 'quantity': i.quantity,
        'price': i.price, 'category': i.category, 'low_stock': i.low_stock
    } for i in items])

@app.route('/api/inventory', methods=['POST'])
def add_inventory():
    user = get_user()
    if not user: return jsonify({'error': 'Login karein!'}), 401
    count = Inventory.query.filter_by(user_email=user['email']).count()
    if not is_premium() and count >= 10:
        return jsonify({'error': 'FREE_LIMIT', 'message': 'Free plan mein sirf 10 items! Premium len.'}), 403
    data = request.json
    item = Inventory(user_email=user['email'], name=data['name'],
                     quantity=data['quantity'], price=data['price'],
                     category=data.get('category', 'General'),
                     low_stock=data.get('low_stock', 5))
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
def delete_inventory(item_id):
    item = Inventory.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
def update_inventory(item_id):
    item = Inventory.query.get(item_id)
    if item:
        data = request.json
        item.quantity = data.get('quantity', item.quantity)
        db.session.commit()
    return jsonify({'success': True})

# ── Stats ──
@app.route('/api/stats', methods=['GET'])
def get_stats():
    user = get_user()
    if not user: return jsonify({'error': 'Login karein!'}), 401
    email = user['email']
    total_invoices  = Invoice.query.filter_by(user_email=email).count()
    paid_invoices   = Invoice.query.filter_by(user_email=email, status='paid').count()
    total_revenue   = db.session.query(db.func.sum(Invoice.total)).filter_by(user_email=email, status='paid').scalar() or 0
    total_expenses  = db.session.query(db.func.sum(Expense.amount)).filter_by(user_email=email).scalar() or 0
    low_stock_items = Inventory.query.filter_by(user_email=email).filter(Inventory.quantity <= Inventory.low_stock).count()
    return jsonify({
        'total_invoices': total_invoices, 'paid_invoices': paid_invoices,
        'total_revenue': round(total_revenue, 2), 'total_expenses': round(total_expenses, 2),
        'net_profit': round(total_revenue - total_expenses, 2),
        'low_stock_items': low_stock_items
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5004)
