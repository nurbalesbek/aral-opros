from flask import Flask, render_template, request, redirect, flash
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Для использования flash-сообщений




# Конфигурация подключения к PostgreSQL
DB_HOST = 'localhost'  # Или хост вашего PostgreSQL сервера
DB_NAME = 'survey_db'  # Имя вашей базы данных
DB_USER = 'postgres'  # Имя пользователя
DB_PASSWORD = '2424'  # Ваш пароль для PostgreSQL

# Функция для получения подключения к PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# Функция инициализации базы данных
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
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
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("База данных и таблица созданы или уже существуют.")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")

# Инициализация базы данных
init_db()

@app.route('/')
def index():
    countries = [
        'Азербайджан', 'Армения', 'Беларусь', 'Казахстан', 'Кыргызстан', 
        'Молдова', 'Россия', 'Таджикистан', 'Туркменистан', 'Узбекистан', 
        'Украина', 'Эстония', 'Латвия', 'Литва', 'Грузия', 'Другое'
    ]
    return render_template('index.html', countries=countries)

@app.route('/submit', methods=['POST'])
def submit():
    fields = ['country', 'gender', 'age', 'with_children', 
              'source', 'travel_mode', 'days', 'accommodation', 'suggestions']
    values = {field: request.form.get(field) for field in fields}
    
    # Проверка данных перед сохранением
    if not all(values.values()):
        flash("Пожалуйста, заполните все поля!")
        return redirect('/')
    
    try:
        # Сохраняем данные в базу данных PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO responses (country, gender, age, with_children, 
                                   source, travel_mode, days, accommodation, suggestions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (values['country'], values['gender'], values['age'], values['with_children'], 
              values['source'], values['travel_mode'], values['days'], values['accommodation'], values['suggestions']))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Ваши ответы успешно отправлены!")
        return redirect('/thank_you')
    except Exception as e:
        flash(f"Ошибка при сохранении данных: {e}")
        return redirect('/')

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/results')
def results():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM responses ORDER BY submitted_at DESC')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('results.html', rows=rows)
    except Exception as e:
        flash(f"Ошибка при получении результатов: {e}")
        return redirect('/')

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000, debug=True)
