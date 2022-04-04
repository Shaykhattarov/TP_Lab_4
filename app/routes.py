import datetime

from flask import render_template, flash, redirect, request, url_for
from flask_login import login_required, login_user, current_user, logout_user

from app import app, db, os, json, requests
from app.forms import LoginForm, CreateUserForm, ChangeUserForm, SelectUserForm, CreateNewsForm
from app.models import User, News
from app.yandex_api import YandexAPI as yapi
from app import login_manager


@app.route('/')
@app.route('/home')
def index():

    img_dir = os.path.join(os.path.dirname(__file__), app.config["YANDEX_API_IMG"])
    json_dir = os.path.join(os.path.dirname(__file__), app.config["YANDEX_API_JSON"])

    count_img = len(os.listdir(img_dir))
    count_json = len(os.listdir(json_dir))

    last_img_dirpath = f'{img_dir}/picture_{count_img - 1}.jpg'
    last_json_dirpath = f'{json_dir}/result_{count_json - 1}.json'

    last_img_htmlpath  = f'{app.config["YANDEX_API_IMG"]}/picture_{count_img - 1}.jpg'

    federal_area = ""
    city = ""

    with open(last_json_dirpath, 'r', encoding='utf-8') as file:
        data = json.load(file)
        country = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['description']
        federal_area = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
            'GeocoderMetaData']['AddressDetails']['Country']["AdministrativeArea"]["AdministrativeAreaName"]
        city = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['name']

    return render_template('index.html', img=last_img_htmlpath, country=country, federal_area=federal_area, city=city)


@app.route('/city-map/<string:city>')
def city_map(city):
    img_dir = os.path.join(os.path.dirname(__file__), app.config["YANDEX_API_IMG"])

    data = yapi.get_pos(city)

    longitude = data['longitude']
    width = data['width']

    data = data['data']

    country = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['description']
    federal_area = \
        data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
            'GeocoderMetaData'][
            'AddressDetails']['Country']["AdministrativeArea"]["AdministrativeAreaName"]
    city = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['name']

    img_name = yapi.get_map(longitude, width)['img_name']
    img_htmlpath = f'{app.config["YANDEX_API_IMG"]}/{img_name}'

    return render_template('search.html', img=img_htmlpath, country=country, federal_area=federal_area, city=city)


@app.route('/profile/', methods=['get', 'post'])
@login_required
def profile():
    if not current_user.is_authenticated:
        return redirect('login')
    form = ChangeUserForm()
    message = ""
    if request.method == 'POST':
        data = dict({
            'name': current_user.user_name,
            'surname': current_user.user_surname,
            'login': current_user.user_email,
            'password': current_user.user_password,
            'old': current_user.user_old,
            'work': current_user.user_work
        })

        new_data = dict({
            'name': form.name.data,
            'surname': form.surname.data,
            'login': form.email.data,
            'password': form.password.data,
            'confirm_password': form.confirm_password.data,
            'old': form.old.data,
            'work': form.work.data
        })

        user = db.session.query(User).filter_by(user_id=current_user.user_id).one()
        if new_data['name'] and new_data['name'] != data['name']:
            data['name'] = new_data['name']
        if new_data['surname'] and new_data['surname'] != data['surname']:
            data['surname'] = new_data['name']
        if new_data['login'] and new_data['login'] != data['login']:
            data['login'] = new_data['login']
        if new_data['old'] and new_data['old'] != data['old']:
            data['old'] = new_data['old']
        if new_data['work'] and new_data['work'] != data['work']:
            data['work'] = new_data['work']
        if not User.check_password(data['password'], new_data['password']) and new_data['password'] == new_data['confirm_password']:
            data['password'] = User.hash_password(new_data['password'])

        user.user_name = data['name']
        user.user_surname = data['surname']
        user.user_email = data['login']
        user.user_password = data['password']
        user.user_old = data['old']
        user.user_work = data['work']

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            message = "Изменение данных в бд прошло с ошибкой!"
            print(e)
        else:
            current_user.user_name = data['name']
            current_user.user_surname = data['surname']
            current_user.user_email = data['login']
            current_user.user_password = data['password']
            current_user.user_old = data['old']
            current_user.user_work = data['work']
            return redirect(url_for('profile'))

    return render_template('profile.html', form=form, message=message)


@app.route('/login/', methods=['post', 'get'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    message = ""
    if request.method == 'POST':
        login = form.email.data
        try:
            user = db.session.query(User).filter(User.user_email == login).first()
            print(user.user_name)
        except Exception as e:
            message = "Пользователь не найден!"
        else:
            if user.user_password is not None and User.check_password(user.user_password, form.password.data):
                login_user(user)
                return redirect(url_for('index'))
            else:
                return redirect(url_for('login'))
    return render_template('auth_form.html', form=form, message=message)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


def does_user_exist(email):
    user = db.session.query(User).filter(User.user_email == email).first()
    if user is None:
        return None
    else:
        return "Такой пользователь уже существует!"


@app.route('/reg/', methods=['post', 'get'])
def registration():
    form = CreateUserForm()
    message = ""
    if form.validate_on_submit():
        data = dict({
            'name': form.name.data,
            'surname': form.surname.data,
            'email': form.email.data,
            'password': User.hash_password(form.password.data),
            'old': form.old.data,
            'work': form.work.data
                    })
        try:
            find_person = does_user_exist(data['email'])
            if find_person is None:
                new_user = User(user_name=data['name'], user_surname=data['surname'], user_email=data['email'], user_password=data['password'], user_old=data['old'], user_work=data['work'], user_img='000.jpg')
                db.session.add(new_user)
                db.session.commit()
            else:
                message = find_person
                raise Exception(message)
        except Exception as e:
            print(e)
        else:
            return redirect(url_for('login'))
    return render_template('reg_form.html', form=form, message=message)


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('login'))


@app.route('/admin-choice/', methods=['get', 'post'])
def admin_choice():
    if current_user.user_email != "admin@admin.ru" and current_user.user_password != "admin":
        return redirect(url_for('registration'))
    select_form = SelectUserForm()
    list_data = list()
    users = db.session.query(User).order_by(User.user_id).all()
    for i in range(len(users)):
        list_data.append((str(users[i].user_id), users[i].user_email))
    select_form.id.default = ['3']
    select_form.id.choices = list_data
    if request.method == "POST":
        print(int(select_form.id.data[0]))
        user_id = int(select_form.id.data[0])
        return redirect(url_for('admin', user_id=user_id))
    return render_template('admin_choice_form.html', select_form=select_form)


@app.route('/admin/', methods=['get', 'post'])
@login_required
def admin():
    if current_user.user_email != "admin@admin.ru" and current_user.user_password != "admin":
        return redirect(url_for('registration'))
    user_id = request.args.get('user_id')
    form = ChangeUserForm()
    message = ""
    try:
        user_response = db.session.query(User).filter(User.user_id == user_id).one()
    except Exception as e:
        print(e)
    else:
        user_info = User()
        user_info.user_id = user_response.user_id
        user_info.user_name = user_response.user_name
        user_info.user_surname = user_response.user_surname
        user_info.user_email = user_response.user_email
        user_info.user_old = user_response.user_old
        user_info.user_work = user_response.user_work

    if request.method == 'POST':
        data = dict({
            'name': user_info.user_name,
            'surname': user_info.user_surname,
            'login': user_info.user_email,
            'old': user_info.user_old,
            'work': user_info.user_work
        })
        new_data = dict({
            'name': form.name.data,
            'surname': form.surname.data,
            'login': form.email.data,
            'old': form.old.data,
            'work': form.work.data
        })

        if new_data['name'] and new_data['name'] != data['name']:
            data['name'] = new_data['name']
        if new_data['surname'] and new_data['surname'] != data['surname']:
            data['surname'] = new_data['surname']
        if new_data['login'] and new_data['login'] != data['login']:
            data['login'] = new_data['login']
        if new_data['old'] and new_data['old'] != data['old']:
            data['old'] = new_data['old']
        if new_data['work'] and new_data['work'] != data['work']:
            data['work'] = new_data['work']

        try:
            update_query = db.session.query(User).filter(User.user_id == user_id).update({User.user_name: data['name'], User.user_surname: data['surname'], User.user_email: data['login'], User.user_old: data['old'], User.user_work: data['work']}, synchronize_session=False)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            message = "Изменение данных в бд прошло с ошибкой!"
            print(e)
        else:
            return redirect(url_for('admin', user_id=user_id))

    return render_template('admin.html', form=form, message=message, data=user_info)


@app.route('/news/', methods=['get', 'post'])
def news():
    news = News()
    news.news_id = '1'
    news.news_text = 'Hello world!'
    news.news_title = 'Hello world!'
    news.news_intro = 'Hello world!'
    news.news_date = '12.03.2022'
    news.news_author = 'Ildan'
    return render_template('news.html', data=news)


@app.route('/my-news/', methods=['get', 'post'])
def my_news():
    pass


@app.route('/create-news/', methods = ['get', 'post'])
def create_news():
    form = CreateNewsForm()
    post = News()
    message = "Все ок!"
    if request.method == 'POST' and  form.validate_on_submit():
        data = dict({
            title: form.title.data,
            intro: form.intro.data,
            text: form.titel.data,
            author: current_user.user_name,
            date: str(datetime.date()),
        })

    return render_template('create_news.html', form=form, message=message)