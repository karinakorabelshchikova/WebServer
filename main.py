# Разработчик  — Карина Корабельщикова.
# Сайт для любителей архитектуры. Возможность посмотреть на здания университетов со всего мира.
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('homepage.html')


@app.route('/about')
def about():
    return render_template('aboutpage.html')


#  Возможно, имеет смысл добавить страницу-обработчик ошибок


@app.route('/<university>')
def university_page(university):
    #  Здесь всё переделать
    parameters = {'university': university}
    return render_template('universitypage.html', **parameters)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')  # Изменить перед сдачей


#  Придумать название для сайта!
