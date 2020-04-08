# Разработчик  — Карина Корабельщикова.
# Сайт для любителей архитектуры. Возможность посмотреть на здания университетов со всего мира.
from flask import Flask, render_template, request, redirect
import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy.ext.declarative as dec
import base64  # Используется для декодирования байтовых картинок

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some_secret_key'

SqlAlchemyBase = dec.declarative_base()


def global_init(db_file):
    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    engine = sa.create_engine(conn_str, echo=False)
    SqlAlchemyBase.metadata.create_all(engine)
    return orm.sessionmaker(bind=engine)


SESSION_MAKER = global_init("universities.sqlite")


class University(SqlAlchemyBase):
    __tablename__ = 'universities'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    about = sa.Column(sa.String, nullable=True)  # Текст статьи
    link_to_wikipedia = sa.Column(sa.String, nullable=True)
    titles = orm.relation('Title', back_populates='university')
    photos = orm.relation('Photo', back_populates='university')

    def __init__(self, about='', link_to_wikipedia=''):
        global SESSION_MAKER
        self.about = about
        self.link_to_wikipedia = link_to_wikipedia
        session = SESSION_MAKER()
        session.add(self)
        session.commit()


def get_bytes_from_image(filename) -> bytes:
    # Функция возвращает изображение в бинарном виде
    with open(filename, 'rb') as f:
        return f.read()


class Photo(SqlAlchemyBase):
    __tablename__ = 'photos'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    university_id = sa.Column(sa.Integer, sa.ForeignKey("universities.id"))
    preview = sa.Column(sa.Boolean, default=False)
    photo = sa.Column(sa.BLOB)  # Изображение хранится бинарно
    formatt = sa.Column(sa.String)
    university = orm.relation('University')

    def __init__(self, university, photo_path, preview=False):
        global SESSION_MAKER
        self.university_id = university
        self.photo = get_bytes_from_image(photo_path)
        self.formatt = photo_path.split('.')[-1]
        self.preview = preview
        session = SESSION_MAKER()
        session.add(self)
        session.commit()


def get_source_from_bytes(photo: Photo):
    #  Деланье из картинки её адрес для атрибута src
    string = base64.b64encode(photo.photo)  # Получаем байты вида b'...'; type: bytes
    string = str(string)  # Делаем из них строку вида 'b'...''; type: str
    string = string[2:][:-1]  # Теперь '...'; type: str
    source = f'data:image/{photo.formatt};base64,' + string
    return source


class Title(SqlAlchemyBase):
    # Т. к. у одного университета может быть несколько названий, создана отдельная таблица
    __tablename__ = 'titles'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    university_id = sa.Column(sa.Integer, sa.ForeignKey("universities.id"))
    is_main = sa.Column(sa.Boolean, default=False)
    title = sa.Column(sa.String)
    university = orm.relation('University')

    def __init__(self, university, title, is_main=False):
        global SESSION_MAKER
        self.university_id = university
        self.title = title
        self.is_main = is_main
        session = SESSION_MAKER()
        session.add(self)
        session.commit()


def get_university_attributes(university: (int, str)):
    # Параметр функции -- название или айди
    session = SESSION_MAKER()
    if type(university) == str:
        if university == 'random':  # Нужна случайная страница
            u = session.query(University).order_by(sa.sql.functions.random()).first()
        else:
            #  Ищем университет по названию, регистр игнорируется
            title = session.query(Title).filter(Title.title.ilike(university)).first()
            if title is not None:
                u = session.query(University).filter(University.id == title.university_id).first()
            else:  # Нет университета с таким названием
                return
    else:
        u = session.query(University).filter(University.id == university).first()
    if u is None:  # Нет университета с таким id
        return
    # Собираем параметры
    parameters = dict()
    # Получаем основное название без изменения регистра.
    parameters['university'] = \
        session.query(Title).filter(Title.university_id == u.id, Title.is_main).first().title
    parameters['about'] = u.about if u.about else ''
    # Получение картинок
    sources = []
    for photo in u.photos:
        source = get_source_from_bytes(photo)
        sources.append(source)
    parameters['photos'] = sources
    parameters['link_to_wikipedia'] = u.link_to_wikipedia if u.link_to_wikipedia else ''
    return parameters


# Тестовый беспредел:

# u = University('''Основан 1917 года. Один из старейших и крупнейших классических университетов
# России, один из центров отечественной науки и культуры. Расположен в Москве. C 1940 года носит
# имя Михаила Васильевича Ломоносова. Полное название — Федеральное государственное бюджетное
# образовательное учреждение высшего образования «Московский государственный университет имени
# М. В. Ломоносова». Широко используется аббревиатура «МГУ». Университет включает в себя 15
# научно-исследовательских институтов, 43 факультета, более 300 кафедр и 6 филиалов (в их числе
# пять зарубежных).''',
# 'https://ru.wikipedia.org/wiki/%D0%9C%D0%BE%D1%81%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B8%D0%B9' + \
# '_%D0%B3%D0%BE%D1%81%D1%83%D0%B4%D0%B0%D1%80%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D1%8B%D0%B9' + \
# '_%D1%83%D0%BD%D0%B8%D0%B2%D0%B5%D1%80%D1%81%D0%B8%D1%82%D0%B5%D1%82'
#                )
# Photo(u.id, 'static/MSU test.jpeg')
# for i in range(1, 10):
#     Photo(u.id, f'static/{i}.jpg', True)
# Title(u.id, 'МГУ')
# Title(u.id, 'Московский государственный университет имени М. В. Ломоносова', True)
# Title(u.id, 'Московский государственный университет им. М. В. Ломоносова')
# Title(u.id, 'Московский Государственный Университет')


def navbar_with_background(func):
    # Это декоратор. Он добавляет в карусель в шапке страницы 3 адреса случайных картинок, у которых
    # параметр preview == True

    def decorated_function(*args, **kwargs):
        # Получение страницы с помощью изначальной функции
        page = func(*args, **kwargs)
        # Получение подходящих картинок
        session = SESSION_MAKER()
        photos = session.query(Photo)  # Все фото, что есть в таблице
        photos = photos.filter(Photo.preview)  # Все превью-фото
        photos = photos.order_by(sa.sql.functions.random())  # Все превью-фото, перемешанные
        photos = photos.limit(3).all()  # Список из трёх случайных превью-фото, что и требовалось
        # Перевод в подходящий формат
        photos = map(get_source_from_bytes, photos)
        # Вставка на страницу
        for ns in ('first', 'second', 'third'):
            page = page.replace(f'insert_{ns}_photo_here', next(photos))
        # Отправка отредактированной страницы
        return page

    # Эта строка убирает ошибки, которые возникают у flask
    decorated_function.__name__ = func.__name__
    return decorated_function


@app.route('/')
@navbar_with_background
def home():
    return render_template('homepage.html')


@app.route('/about')
@navbar_with_background
def about():
    return render_template('aboutpage.html')


#  Имеет смысл добавить страницу-обработчик ошибок


@app.route('/search')
@navbar_with_background
def find_university_page():
    search = request.args.get('find')
    if not search:  # значение пустое
        # остаться где были и ничего не делать
        return '<script>document.location.href = document.referrer</script>'
    parameters = get_university_attributes(search)
    if parameters is None:  # Нет в бд
        return '<script>document.location.href = document.referrer</script>'
    return render_template('universitypage.html', **parameters)


@app.route('/<university>')
@navbar_with_background
def university_page(university):
    parameters = get_university_attributes(university)
    if not parameters:
        # В бд нет такого университета
        return '<script>document.location.href = document.referrer</script>'
    return render_template('universitypage.html', **parameters)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')  # Изменить перед сдачей


#  Придумать название для сайта!
