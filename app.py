from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import sqlite3
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)
bcrypt = Bcrypt(app)

# Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-pro")

# --- Database setup ---
def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL
                        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS notes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            content TEXT,
                            FOREIGN KEY(user_id) REFERENCES users(id)
                        )''')

init_db()

# --- Routes ---
@app.route("/")
def home():
    if "user_id" in session:
        with sqlite3.connect("database.db") as conn:
            notes = conn.execute("SELECT content FROM notes WHERE user_id=?", (session["user_id"],)).fetchall()
        return render_template("index.html", notes=notes)
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode('utf-8')
        try:
            with sqlite3.connect("database.db") as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
            return redirect("/login")
        except sqlite3.IntegrityError:
            return "Username already exists"
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with sqlite3.connect("database.db") as conn:
            user = conn.execute("SELECT id, password FROM users WHERE username=?", (username,)).fetchone()
        if user and bcrypt.check_password_hash(user[1], password):
            session["user_id"] = user[0]
            return redirect("/")
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/save", methods=["POST"])
def save():
    if "user_id" not in session:
        return redirect("/login")
    data = request.get_json()
    text = data.get("text", "")
    with sqlite3.connect("database.db") as conn:
        conn.execute("INSERT INTO notes (user_id, content) VALUES (?, ?)", (session["user_id"], text))
        conn.commit()
    return jsonify({"status": "saved"})

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        prompt = data.get("text", "")
        if not prompt:
            return jsonify({"error": "No text provided"}), 400
        response = model.generate_content(prompt)
        return jsonify({"result": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
