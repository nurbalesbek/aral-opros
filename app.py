import os
from flask import Flask, render_template, request, redirect, flash
import psycopg2

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Локальные настройки (для dev)
DB_HOST = 'localhost'
DB_NAME = 'survey_db'
DB_USER = 'postgres'
DB_PASSWORD = '2424'

def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return psycopg2.connect(db_url, sslmode='require')
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS responses (
        id SERIAL PRIMARY KEY,
        country TEXT,
        gender TEXT,
        age TEXT,
        with_children TEXT,
        source TEXT,
        travel_mode TEXT,
        days TEXT,
        accommodation TEXT,
        suggestions TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    """)
    conn.commit()
    cur.close(); conn.close()

init_db()

@app.route('/')
def index():
    countries = ['Азербайджан','Армения','Беларусь','Казахстан','Кыргызстан',
                 'Молдова','Россия','Таджикистан','Туркменистан','Узбекистан',
                 'Украина','Эстония','Латвия','Литва','Грузия','Другое']
    return render_template('index.html', countries=countries)

@app.route('/submit', methods=['POST'])
def submit():
    fields = ['country','gender','age','with_children',
              'source','travel_mode','days','accommodation','suggestions']
    data = [request.form.get(f) for f in fields]
    if not all(data[:-1]):  # suggestions можно оставить пустым
        flash("Заполните все поля!")
        return redirect('/')
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("""
      INSERT INTO responses
        (country,gender,age,with_children,source,
         travel_mode,days,accommodation,suggestions)
      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """, data)
    conn.commit(); cur.close(); conn.close()
    return redirect('/thank_you')

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

if __name__=='__main__':
    app.run(debug=True)
