from flask import Flask, render_template, request, redirect, jsonify, session, current_app
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash
import os
from os import path
import sqlite3
import re

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'секретно-секретный секрет')
app.config['DB_TYPE'] = os.getenv('DB_TYPE', 'postgres')

def db_connect():
    if current_app.config['DB_TYPE'] == 'postgres':
        conn = psycopg2.connect(
            host='127.0.0.1',
            database='tinder',
            user='sergey',
            password='123',
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
    else:
        dir_path = path.dirname(path.realpath(__file__))
        db_path = path.join(dir_path, "database.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

    return conn, cur

def db_close(conn, cur):
    conn.commit()
    cur.close()
    conn.close()

# Проверка пароля
def is_valid_username_password(value):
    if not value:
        return False
    return bool(re.match(r'^[A-Za-z0-9!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]+$', value))


@app.route('/')
def index():
    return render_template('register_login.html')


@app.route('/rest-api/users/registration', methods=['POST'])
def registration():
    data = request.get_json()
  
    username = data.get('username')
    password = data.get('password')

    if not username:
        return {'username': 'Придумайте свой ник'}, 400
    if not password:
        return {'password': 'Заполните пароль'}, 400

    if not is_valid_username_password(username):
        return {'username': 'Логин должен состоять только из латинских букв, цифр и знаков препинания'}, 400
    if not is_valid_username_password(password):
        return {'password': 'Пароль должен состоять только из латинских букв, цифр и знаков препинания'}, 400

    password_hash = generate_password_hash(password)
    conn, cur = db_connect()

    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (username, password_hash)
        )
        new_user_id = cur.fetchone()['id']
    else:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password_hash)
        )
        new_user_id = cur.lastrowid
    
    db_close(conn, cur)
    return {"index": new_user_id}, 201


@app.route('/rest-api/users/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username:
        return {'username': 'Введите никнэйм'}, 400
    if not password:
        return {'password': 'Введите пароль'}, 400

    if not is_valid_username_password(username):
        return {'username': 'Логин должен состоять только из латинских букв, цифр и знаков препинания'}, 400
    if not is_valid_username_password(password):
        return {'password': 'Пароль должен состоять только из латинских букв, цифр и знаков препинания'}, 400

    conn, cur = db_connect()
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()  
    else:
        cur.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        user = cur.fetchone()

    if not user:
        db_close(conn, cur)
        return {'username': 'Пользователь не найден'}, 400

    user_id = user['id']
    username = user['username']
    password_hash = user['password']

    if not check_password_hash(password_hash, password):
        db_close(conn, cur)
        return {'password': 'Неверный пароль'}, 400

    session['user_id'] = user_id
    session['username'] = username
    db_close(conn, cur)
    return {}, 200


@app.route('/rest-api/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')


@app.route('/main')
def main_page():
    if 'user_id' not in session:
        return redirect('/')  
    
    user_id = session['user_id']
    conn, cur = db_connect()

    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("SELECT * FROM profiles WHERE user_id = %s", (user_id,))
    else:
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    
    profile = cur.fetchone()
    profile_filled = bool(profile)

    db_close(conn, cur)

    if profile:
        profile = dict(profile)  

        gender_map = {
            "male": "мужской",
            "female": "женский"
        }
        profile['gender'] = gender_map.get(profile['gender'], profile['gender'])
        looking_for_map = {
            "male": "мужской",
            "female": "женский"
        }
        profile['looking_for'] = looking_for_map.get(profile['looking_for'], profile['looking_for'])

    return render_template('main.html', username=session['username'], profile=profile, profile_filled=profile_filled)


@app.route('/rest-api/profiles', methods=['POST'])
def add_profile():
    user_id = session['user_id'] 

    if 'user_id' not in session:
        return {'message': 'Не авторизован'}, 403

    name = request.form.get('name')
    age = request.form.get('age')
    gender = request.form.get('gender')
    looking_for = request.form.get('looking_for')
    about = request.form.get('about', '')

    if not name or not age or not gender or not looking_for:
        return {'message': 'Заполните все обязательные поля'}, 400

    conn, cur = db_connect()
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute(
            """
            INSERT INTO profiles (user_id, name, age, gender, looking_for, about)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, name, age, gender, looking_for, about),
        )
    else:
        cur.execute(
            """
            INSERT INTO profiles (user_id, name, age, gender, looking_for, about)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, age, gender, looking_for, about),
        )
    db_close(conn, cur)

    return {'message': 'Профиль успешно добавлен'}, 201


@app.route('/rest-api/profiles', methods=['PUT'])
def update_profile():
    if 'user_id' not in session:
        return {'message': 'Не авторизован'}, 403

    user_id = session['user_id']
    name = request.form.get('name')
    age = request.form.get('age')
    gender = request.form.get('gender')
    looking_for = request.form.get('looking_for')
    about = request.form.get('about', '')
    is_hidden = request.form.get('is_hidden') == 'true'

    if not name or not age or not gender or not looking_for:
        return {'message': 'Заполните все обязательные поля'}, 400

    conn, cur = db_connect()

    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute(
            """
            UPDATE profiles
            SET name = %s, age = %s, gender = %s, looking_for = %s, about = %s, is_hidden = %s
            WHERE user_id = %s
            """,
            (name, age, gender, looking_for, about, is_hidden, user_id),
        )
    else:
        cur.execute(
            """
            UPDATE profiles
            SET name = ?, age = ?, gender = ?, looking_for = ?, about = ?, is_hidden = ?
            WHERE user_id = ?
            """,
            (name, age, gender, looking_for, about, is_hidden, user_id),
        )

    db_close(conn, cur)
    return {'message': 'Профиль успешно обновлен'}, 200


@app.route('/rest-api/profiles/delete', methods=['DELETE'])
def delete_profile():
    if 'user_id' not in session:
        return {'message': 'Не авторизован'}, 403

    user_id = session['user_id']

    conn, cur = db_connect()
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("DELETE FROM profiles WHERE user_id = %s", (user_id,))
    else:
        cur.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
    db_close(conn, cur)
    session.clear()
    return {'message': 'Аккаунт успешно удален'}, 200


@app.route('/rest-api/search', methods=['GET'])
def search_profiles():
    if 'user_id' not in session:
        return {'message': 'Не авторизован'}, 403

    search_name = request.args.get('name', '').strip()
    search_age = request.args.get('age')
    offset = int(request.args.get('offset', 0)) 
    limit = 3  

    user_id = session['user_id']
    conn, cur = db_connect()

    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("""
            SELECT gender, looking_for FROM profiles WHERE user_id = %s
        """, (user_id,))
    else:
        cur.execute("""
            SELECT gender, looking_for FROM profiles WHERE user_id = ?
        """, (user_id,))
    
    user_profile = cur.fetchone()
    if not user_profile:
        db_close(conn, cur)
        return {'message': 'Профиль не найден'}, 404
    
    user_gender = user_profile['gender']
    user_looking_for = user_profile['looking_for']

    if current_app.config['DB_TYPE'] == 'postgres':
        query = """
            SELECT name, age, gender, about
            FROM profiles
            WHERE is_hidden = FALSE
            AND gender = %s
            AND looking_for = %s
        """
        params = [user_looking_for, user_gender]

        if search_name:
            query += " AND name ILIKE %s"
            params.append(f"%{search_name}%")

        if search_age:
            query += " AND age = %s"
            params.append(search_age)

        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

    else:
        query = """
            SELECT name, age, gender, about
            FROM profiles
            WHERE is_hidden = 0
            AND gender = ?
            AND looking_for = ?
        """
        params = [user_looking_for, user_gender]

        if search_name:
            query += " AND name LIKE ?"
            params.append(f"%{search_name}%")

        if search_age:
            query += " AND age = ?"
            params.append(search_age)

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    cur.execute(query, tuple(params))
    results = cur.fetchall()
    db_close(conn, cur)

    return jsonify([dict(row) for row in results]), 200