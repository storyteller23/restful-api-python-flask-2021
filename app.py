import sqlite3
from flask import (Flask, render_template, request,
                   session, redirect, url_for, jsonify)
from random import choice

app = Flask(__name__)
app.secret_key = "SECRETKEY"
DATABASE = "restapiapp.sqlite3"


# Генерация API ключа
def key_generate():
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    key = ""
    for _ in range(8):
        key += choice(alpha)
    return key


# Домашняя страница
@app.route("/", methods=["get"])
def homepage():
    if "username" not in session:
        return redirect(url_for("login"))
    with sqlite3.connect(DATABASE) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT api_key FROM users\
                         WHERE username = '{session['username']}'")
        api_key = cursor.fetchone()[0]
    user = session["username"]

    return render_template("index.html", user=user, api_key=api_key)


# Вход на сайт
@app.route('/login/', methods=['post', 'get'])
def login():
    if "username" in session:
        return redirect(url_for("homepage"))
    message = ''
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        with sqlite3.connect(DATABASE) as con:
            cursor = con.cursor()
            cursor.execute(f"SELECT * FROM users\
                             WHERE username = '{username}' \
                             AND password = '{password}'")
            result = cursor.fetchone()
            if result is not None:
                print(result[-1])
                session["username"] = result[1]
                return redirect(url_for("homepage"))
            else:
                message = "Неправильный логин или пароль!!!"

    return render_template("login.html", message=message)


# Регистрация
@app.route("/register/", methods=["post", "get"])
def register():
    if "login" in session:
        return redirect(url_for("homepage"))
    message = ''
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        confirm = request.form['confirm']
        if password != confirm:
            message = "Пароли не совпадают!!!"
        else:
            with sqlite3.connect(DATABASE) as con:
                cursor = con.cursor()
                while 1:
                    api_key = key_generate()
                    cursor.execute(f"SELECT username FROM users \
                                    WHERE api_key = '{api_key}'")
                    if cursor.fetchone() is None:
                        break
                cursor = con.cursor()
                cursor.execute(f"SELECT username FROM users \
                                WHERE username = '{username}'")
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO \
                                    users(username, password, api_key) \
                                    VALUES (?, ?, ?)",
                                   (username, password, api_key))
                    cursor.execute(f"CREATE TABLE {username}( \
                                        id INTEGER PRIMARY KEY AUTOINCREMENT, \
                                        fullname TEXT, \
                                        number TEXT\
                                    )")
                    con.commit()
                    message = "Пользователь успешно создан!"
                else:
                    message = "Пользователь с таким именем существует..."

    return render_template("register.html", message=message)


# Закрыть сессию
@app.route('/close_session/')
def close_session():
    session.pop("username", None)
    return redirect(url_for("login"))


# Реализация API
# Получение всех данных из базы GET-запрос
@app.route("/api/<api_key>/", methods=["GET"])
def get_all_data(api_key):
    api_key = api_key.upper()
    table_name = ""
    data = []
    with sqlite3.connect(DATABASE) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT username FROM users\
                        WHERE api_key = '{api_key}'")
        result = cursor.fetchone()
        if result is None:
            return {"message": "Invalid API-key"}, 404
        table_name = result[0]

        cursor.execute(f"SELECT * FROM {table_name}")
        for row in cursor.fetchall():
            data.append({
                "id": row[0],
                "fullname": row[1],
                "number": row[2]
                })
    return jsonify(data)


# Получение данных указаного id GET-запрос
@app.route("/api/<api_key>/<int:id>", methods=["GET"])
def get_data(api_key, id):
    api_key = api_key.upper()
    table_name = ""
    data = []
    with sqlite3.connect(DATABASE) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT username FROM users\
                        WHERE api_key = '{api_key}'")
        result = cursor.fetchone()
        if result is None:
            return {"message": "Invalid API-key"}, 404
        table_name = result[0]

        cursor.execute(f"SELECT * FROM {table_name} \
                        WHERE id = {id}")
        result = cursor.fetchone()
        if result is None:
            return {"message": "No rows with this id"}, 400
        data.append({
            "id": result[0],
            "fullname": result[1],
            "number": result[2]
            })
    return jsonify(data)


# Добавление данных в базу POST-запрос
@app.route("/api/<api_key>/", methods=["POST"])
def add_data(api_key):
    api_key = api_key.upper()
    table_name = ""
    new_one = request.json
    fullname = new_one["fullname"] if "fullname" in new_one else ""
    number = new_one["number"] if "number" in new_one else ""

    with sqlite3.connect(DATABASE) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT username FROM users\
                        WHERE api_key = '{api_key}'")
        result = cursor.fetchone()
        if result is None:
            return {"message": "Invalid API-key"}, 404
        table_name = result[0]

        cursor.execute(f"INSERT INTO {table_name}(fullname, number) \
                        VALUES('{fullname}', '{number}')")
    return {"message": "New row added!"}


# Изменение записи в базе по id PUT-запрос
@app.route("/api/<api_key>/<int:id>", methods=["PUT"])
def update_data(api_key, id):
    api_key = api_key.upper()
    table_name = ""
    new_data = request.json
    new_fullname = new_data["fullname"] if "fullname" in new_data else None
    new_number = new_data["number"] if "number" in new_data else None

    with sqlite3.connect(DATABASE) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT username FROM users\
                        WHERE api_key = '{api_key}'")
        result = cursor.fetchone()
        if result is None:
            return {"message": "Invalid API-key"}, 404
        table_name = result[0]
        cursor.execute(f"SELECT * FROM {table_name} \
                        WHERE id = {id}")
        result = cursor.fetchone()
        print(result)
        if result is None:
            return {"message": "No rows with this id"}, 400

        if new_fullname:
            cursor.execute(f"UPDATE {table_name} SET fullname = '{new_fullname}' \
                            WHERE id = {id}")
        if new_number:
            cursor.execute(f"UPDATE {table_name} SET number = '{new_number}' \
                            WHERE id = {id}")
        if not new_fullname and not new_number:
            return {"message": "No new data"}, 400
    return {"message": "This row updated"}


# Удаление записи в базе по id DELETE-запрос
@app.route("/api/<api_key>/<int:id>", methods=["DELETE"])
def delete_data(api_key, id):
    api_key = api_key.upper()
    table_name = ""
    with sqlite3.connect(DATABASE) as con:
        cursor = con.cursor()
        cursor.execute(f"SELECT username FROM users\
                        WHERE api_key = '{api_key}'")
        result = cursor.fetchone()
        if result is None:
            return {"message": "Invalid API-key"}, 404
        table_name = result[0]
        cursor.execute(f"SELECT * FROM {table_name} \
                        WHERE id = {id}")
        result = cursor.fetchone()
        print(result)
        if result is None:
            return {"message": "No rows with this id"}, 400
        cursor.execute(f"DELETE FROM {table_name} WHERE id = {id}")

    return {"message": "This row deleted"}


@app.errorhandler(500)
def internal_error(error):
    return redirect(url_for("close_session"))


if __name__ == "__main__":
    app.run()
