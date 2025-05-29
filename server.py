from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)

# JWT конфиг
app.config['JWT_SECRET_KEY'] = 'super-secret-key-123'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_COOKIE_SECURE'] = False

jwt = JWTManager(app)

# БД конфиг
DB_CONFIG = {
    'dbname': 'db1',
    'user': 'postgres',
    'password': '123',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            quantity INTEGER NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

def fetch_products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, quantity FROM products")
    products = [{'id': r[0], 'name': r[1], 'price': float(r[2]), 'quantity': r[3]} for r in cur.fetchall()]
    cur.close()
    conn.close()
    return products

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="Введите имя пользователя и пароль")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not check_password_hash(user[0], password):
            return render_template('login.html', error="Неверные данные для входа")

        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        # Для примера можно сохранить токены в куки или передать в шаблон
        # Тут просто редирект на главную или страницу каталога
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('register.html', error="Введите имя пользователя и пароль")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return render_template('register.html', error="Пользователь с таким именем уже существует")

        password_hash = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('login_page'))
    return render_template('register.html')

# API аутентификация 

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"msg": "Username already exists"}), 400

    password_hash = generate_password_hash(password)
    cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
    conn.commit()
    cur.close()
    conn.close()

    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)
    return jsonify(access_token=access_token, refresh_token=refresh_token), 200

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not check_password_hash(user[0], password):
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)
    return jsonify(access_token=access_token, refresh_token=refresh_token), 200

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    return jsonify({"msg": "Refresh endpoint is open (no token required)"}), 200


@app.route('/api/protected', methods=['GET'])
@jwt_required()
def api_protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


@app.route('/api/products', methods=['GET'])
def get_products():
    products = fetch_products()
    return jsonify(products=products), 200

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    quantity = data.get('quantity')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, price, quantity) VALUES (%s, %s, %s)", (name, price, quantity))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(msg="Product added"), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    quantity = data.get('quantity')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE products SET name = %s, price = %s, quantity = %s WHERE id = %s",
        (name, price, quantity, product_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(msg="Product updated"), 200

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(msg="Product deleted"), 200

# Страницы

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/catalog')
def catalog():
    products = fetch_products()
    return render_template('catalog.html', products=products)

@app.route('/about')
def about():
    return render_template('about.html')

# Обработчики ошибок JWT

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"msg": "Token has expired"}), 401

@app.errorhandler(401)
def custom_401(error):
    return jsonify({"msg": "Unauthorized"}), 401

if __name__ == '__main__':
    app.run(debug=True)
