import sqlite3
from datetime import datetime

DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT,
        purpose TEXT,
        person_to_meet TEXT,
        checkin_time TEXT,
        checkout_time TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_visitor(name, contact, purpose, person_to_meet):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    checkin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO visitors (name, contact, purpose, person_to_meet, checkin_time) VALUES (?, ?, ?, ?, ?)",
              (name, contact, purpose, person_to_meet, checkin))
    conn.commit()
    conn.close()

def get_visitors():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM visitors ORDER BY checkin_time DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def checkout_visitor(visitor_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    checkout = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE visitors SET checkout_time = ? WHERE id = ?", (checkout, visitor_id))
    conn.commit()
    conn.close()
from flask import Flask, render_template, request, redirect, url_for
import models

app = Flask(__name__)

# Initialize database
models.init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    contact = request.form['contact']
    purpose = request.form['purpose']
    person_to_meet = request.form['person_to_meet']
    models.add_visitor(name, contact, purpose, person_to_meet)
    return redirect(url_for('visitors'))

@app.route('/visitors')
def visitors():
    data = models.get_visitors()
    return render_template('visitors.html', visitors=data)

@app.route('/checkout/<int:vid>')
def checkout(vid):
    models.checkout_visitor(vid)
    return redirect(url_for('visitors'))

if __name__ == '__main__':
    app.run(debug=True)
