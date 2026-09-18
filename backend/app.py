from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.update(MYSQL_HOST='localhost', MYSQL_USER='root', MYSQL_PASSWORD='', MYSQL_DB='smart_electronics', MYSQL_CURSORCLASS='DictCursor', SECRET_KEY='change-this-secret')
mysql = MySQL(app)
CORS(app)

def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization','').replace('Bearer ','')
        try: user = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except Exception: return jsonify(error='Login required'), 401
        return fn(user, *args, **kwargs)
    return wrapper

@app.get('/api/health')
def health(): return jsonify(status='ok')

@app.post('/api/register')
def register():
    data=request.get_json() or {}; name=data.get('name','').strip(); email=data.get('email','').strip().lower(); password=data.get('password','')
    if not name or not email or len(password)<6: return jsonify(error='Name, email and 6+ character password are required'),400
    cur=mysql.connection.cursor(); cur.execute('SELECT id FROM users WHERE email=%s',(email,))
    if cur.fetchone(): cur.close(); return jsonify(error='Email already registered'),409
    cur.execute('INSERT INTO users(name,email,password) VALUES(%s,%s,%s)',(name,email,generate_password_hash(password))); mysql.connection.commit(); cur.close()
    return jsonify(message='Registration successful'),201

@app.post('/api/login')
def login():
    data=request.get_json() or {}; cur=mysql.connection.cursor(); cur.execute('SELECT id,name,email,password,role FROM users WHERE email=%s',(data.get('email','').lower(),)); user=cur.fetchone(); cur.close()
    if not user or not check_password_hash(user['password'],data.get('password','')): return jsonify(error='Invalid credentials'),401
    token=jwt.encode({'id':user['id'],'role':user['role'],'exp':datetime.utcnow()+timedelta(days=2)},app.config['SECRET_KEY'],algorithm='HS256')
    user.pop('password'); return jsonify(token=token,user=user)

@app.get('/api/products')
def products():
    q=request.args.get('q',''); category=request.args.get('category',''); cur=mysql.connection.cursor(); sql='SELECT * FROM products WHERE (name LIKE %s OR brand LIKE %s)'; params=[f'%{q}%',f'%{q}%']
    if category: sql+=' AND category=%s'; params.append(category)
    sql+=' ORDER BY id DESC'; cur.execute(sql,params); rows=cur.fetchall(); cur.close(); return jsonify(rows)

@app.get('/api/products/<int:pid>')
def product(pid):
    cur=mysql.connection.cursor(); cur.execute('SELECT * FROM products WHERE id=%s',(pid,)); row=cur.fetchone(); cur.close(); return (jsonify(row),200) if row else (jsonify(error='Not found'),404)

@app.post('/api/orders')
@token_required
def create_order(user):
    data=request.get_json() or {}; items=data.get('items',[]); address=data.get('address','').strip(); payment=data.get('payment_method','COD')
    if not items or not address: return jsonify(error='Items and address are required'),400
    cur=mysql.connection.cursor(); total=0; checked=[]
    for item in items:
        cur.execute('SELECT id,price,stock FROM products WHERE id=%s',(item.get('product_id'),)); p=cur.fetchone()
        qty=int(item.get('quantity',1));
        if not p or p['stock']<qty: cur.close(); return jsonify(error='Product unavailable'),400
        total+=float(p['price'])*qty; checked.append((p,qty))
    cur.execute('INSERT INTO orders(user_id,total_amount,address,payment_method) VALUES(%s,%s,%s,%s)',(user['id'],total,address,payment)); oid=cur.lastrowid
    for p,qty in checked:
        cur.execute('INSERT INTO order_items(order_id,product_id,quantity,price) VALUES(%s,%s,%s,%s)',(oid,p['id'],qty,p['price'])); cur.execute('UPDATE products SET stock=stock-%s WHERE id=%s',(qty,p['id']))
    mysql.connection.commit(); cur.close(); return jsonify(order_id=oid,total=total),201

@app.get('/api/orders')
@token_required
def orders(user):
    cur=mysql.connection.cursor(); cur.execute('SELECT * FROM orders WHERE user_id=%s ORDER BY id DESC',(user['id'],)); rows=cur.fetchall(); cur.close(); return jsonify(rows)

@app.get('/api/admin/orders')
@token_required
def admin_orders(user):
    if user.get('role')!='admin': return jsonify(error='Admin only'),403
    cur=mysql.connection.cursor(); cur.execute('SELECT o.*,u.name,u.email FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC'); rows=cur.fetchall(); cur.close(); return jsonify(rows)

if __name__=='__main__': app.run(host='0.0.0.0',debug=True)
