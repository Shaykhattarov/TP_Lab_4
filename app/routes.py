from datetime import date
import datetime
from flask import render_template, flash, redirect, request, url_for, jsonify, abort, make_response
from flask_login import login_required, login_user, current_user, logout_user

from app import app, db, os, json
from app.forms import LoginForm, CreateUserForm, ChangeUserForm, SelectUserForm, CreateNewsForm, ChangeNewsForm, SelectNewsForm
from app.models import User, News, Category, UserAuthorizationLog, NewsCreatingLog
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
            'name': current_user.name,
            'surname': current_user.surname,
            'login': current_user.email,
            'password': current_user.password,
            'old': current_user.old,
            'work': current_user.work
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

        user = db.session.query(User).filter_by(id=current_user.id).one()
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

        user.name = data['name']
        user.surname = data['surname']
        user.email = data['login']
        user.password = data['password']
        user.old = data['old']
        user.work = data['work']

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            message = "Изменение данных в бд прошло с ошибкой!"
            print(e)
        else:
            current_user.name = data['name']
            current_user.surname = data['surname']
            current_user.email = data['login']
            current_user.password = data['password']
            current_user.old = data['old']
            current_user.work = data['work']
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
            user = db.session.query(User).filter(User.email == login).first()
        except Exception as e:
            message = "Пользователь не найден!"
        else:
            if user.password is not None and User.check_password(user.password, form.password.data):
                login_user(user)
                date_now = datetime.datetime.now()
                user_log = UserAuthorizationLog(user_id=user.id, username=user.name, date=date_now)
                try:
                    db.session.add(user_log)
                    db.session.commit()
                except Exception as err:
                    print(err)
                return redirect(url_for('index'))
            else:
                return redirect(url_for('login'))
    return render_template('auth_form.html', form=form, message=message)


@login_manager.user_loader
def load_user(id):
    return db.session.query(User).get(id)


def does_user_exist(email):
    user = db.session.query(User).filter(User.email == email).first()
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
                new_user = User(name=data['name'], surname=data['surname'], email=data['email'], password=data['password'], old=data['old'], work=data['work'], img='000.jpg')
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
    if current_user.email != "admin@admin.ru" and current_user.password != "admin":
        return redirect(url_for('registration'))
    select_form = SelectUserForm()
    list_data = list()
    users = db.session.query(User).order_by(User.id).all()
    for i in range(len(users)):
        list_data.append((str(users[i].id), users[i].email))
    select_form.id.default = ['3']
    select_form.id.choices = list_data
    if request.method == "POST":
        id = int(select_form.id.data[0])
        return redirect(url_for('admin', user_id=id))
    return render_template('admin_choice_form.html', select_form=select_form)


@app.route('/admin/', methods=['get', 'post'])
@login_required
def admin():
    if current_user.email != "admin@admin.ru" and current_user.password != "admin":
        return redirect(url_for('registration'))
    id = request.args.get('user_id')
    form = ChangeUserForm()
    message = ""
    try:
        user_response = db.session.query(User).filter(User.id == id).one()
    except Exception as e:
        print(e)
    else:
        user_info = User()
        user_info.id = user_response.id
        user_info.name = user_response.name
        user_info.surname = user_response.surname
        user_info.email = user_response.email
        user_info.old = user_response.old
        user_info.work = user_response.work

    if request.method == 'POST':
        data = dict({
            'name': user_info.name,
            'surname': user_info.surname,
            'login': user_info.email,
            'old': user_info.old,
            'work': user_info.work
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
            update_query = db.session.query(User).filter(User.id == id).update({User.name: data['name'], User.surname: data['surname'], User.email: data['login'], User.old: data['old'], User.work: data['work']}, synchronize_session=False)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            message = "Изменение данных в бд прошло с ошибкой!"
            print(e)
        else:
            return redirect(url_for('admin', user_id=id))

    return render_template('admin.html', form=form, message=message, data=user_info)


@app.route('/news/', methods=['get', 'post'])
@app.route('/news/<int:page>', methods=['get', 'post'])
def news(page=1):
    news = list()
    posts = str()

    try:
        posts = db.session.query(News, Category.name).join(Category).filter(News.title != None).order_by(News.date).paginate(page, app.config['POSTS_PER_PAGE'], False)
    except Exception as err:
        print(err)

    return render_template('news.html', posts=posts)


@app.route('/author/', methods=['get', 'post'])
@app.route('/author/<author>/', methods=['get', 'post'])
@app.route('/author/<author>', methods=['get', 'post'])
@app.route('/author/<author>/<int:page>', methods=['get', 'post'])
def user_news(author, page=1):
    posts = str()

    try:
        posts = db.session.query(News, Category.name).join(Category).filter(News.author == author).filter(News.title != None).order_by(News.date).paginate(page, app.config['POSTS_PER_PAGE'], False)
    except Exception as err:
        print(err)

    return render_template('news.html', posts=posts)


@app.route('/category', methods=['get', 'post'])
@app.route('/category/<category>', methods=['get', 'post'])
@app.route('/category/<category>/', methods=['get', 'post'])
@app.route('/category/<category>/<int:page>', methods=['get', 'post'])
def category_news(category, page=1):
    posts = list()

    try:
        posts = db.session.query(News, Category.name).join(Category).filter(News.title != None).filter(Category.name == category).order_by(News.date).paginate(page, app.config["POSTS_PER_PAGE"], False)
    except Exception as err:
        print(err)
    else:
        if not posts.items or len(posts.items) == 0:
            redirect(url_for('news'))

    return render_template('news.html', posts=posts)


@app.route('/create-news/', methods = ['get', 'post'])
@login_required
def create_news():
    form = CreateNewsForm()
    post = News()
    category_list = list()
    message = ''

    try:
        categories = db.session.query(Category).order_by(Category.id).all()
        for category in categories:
            category_list.append((str(category.id), category.name))
        form.category.default = ['1']
        form.category.choices = category_list
    except Exception as err:
        message = "Произошла ошибка!"
        print(f'Ошибка: {err}')

    if request.method == "POST":
        image_url = str()
        file_url = str()

        post.user_id = current_user.id
        post.title = form.title.data
        post.intro = form.intro.data
        post.text = form.text.data
        post.category_id = int(form.category.data[0])
        post.author = current_user.name
        post.date = date.today()

        if form.img.data:
            image = form.img.data
            image_url = os.path.join(app.config['UPLOADED_NEWS_PHOTO'], image.filename)
            image.save(image_url)
            post.img = f'/data/news_img/{image.filename}'
        if form.file.data:
            file = form.file.data
            file_url = os.path.join(app.config['UPLOADED_NEWS_FILE'], file.filename)
            file.save(file_url)
            post.file = f'/data/news_files/{file.filename}'
        else:
            file_url = None

        if post.title and post.title != None:
            try:
                db.session.add(post)
                db.session.commit()
            except Exception as err:
                message = "Произошла ошибка!"
                print(err)
            else:
                message = "Пост создан!"
                news_log = NewsCreatingLog(author_id=post.user_id, author_name=post.author, news_title=post.title, date=datetime.datetime.now())
                try:
                    db.session.add(news_log)
                    db.session.commit()
                except Exception as err:
                    print(err)

    return render_template('create_news.html', form=form, message=message)


@app.route('/select-change-post/', methods=['get', 'post'])
@login_required
def select_change_post():
    if current_user.email != "admin@admin.ru" and current_user.password != "admin":
        return redirect(url_for('index'))

    form = SelectNewsForm()
    posts = list()

    try:
        response = db.session.query(News).filter(News.title != None).order_by(News.date).all()
        for post in response:
            posts.append((str(post.id), post.title))
        form.post.default = ['1']
        form.post.choices = posts
    except Exception as err:
        print(err)
    else:
        if request.method == "POST":
            post_id = int(form.post.data[0])
            return redirect(url_for('change_news', post_id=str(post_id)))

    return render_template('admin_choice_news_form.html', form=form)

@app.route('/change-news/', methods = ['get', 'post' ])
def change_news():
    if current_user.email != "admin@admin.ru" and current_user.password != "admin":
        return redirect(url_for('index'))
    post_id = request.args.get('post_id')
    form = ChangeNewsForm()
    category_list = list()
    try:
        post = db.session.query(News, Category.name).join(Category).filter(News.title != None).filter(News.id == post_id).order_by(News.date).first()
        categories = db.session.query(Category).order_by(Category.id).all()
        for category in categories:
            category_list.append((str(category.id), category.name))
        form.category.default = ['1']
        form.category.choices = category_list
    except Exception as err:
        print(err)
    else:
        if request.method == "POST":
            new_category = int(form.category.data[0])

            try:
                update_query = db.session.query(News).filter(News.id == post_id).update(
                    {News.category_id: new_category}, synchronize_session=False)
                db.session.commit()
            except Exception as err:
                db.session.rollback()
                print(err)
            else:
                return redirect(url_for('select_change_post'))

    return render_template('change_news.html', post=post, form=form)


@app.route('/api/news', methods = ['GET'])
def get_all_news():
    domen = 'http://127.0.0.1:5000'
    posts = list()
    try:
        posts = db.session.query(News, Category.name).join(Category).filter(News.title != None).order_by(
            News.date).all()
    except Exception as err:
        print(err)
        abort(404)
    else:
        news_list = list()
        news_lis = list()
        for post, category in posts:
            news_list.append({
                'title': post.title,
                'intro': post.intro,
                'text': post.text,
                'author': post.author,
                'img': f'{domen}/static{post.img}',
                'file_url': f'{domen}/static{post.file}',
                'date': post.date,
                'category': category
            })
        if len(news_list) == 0:
            abort(404)
    return jsonify({ 'news' : news_list}), 200


@app.route('/api/news/category/<string:category>')
def get_category_news(category):
    domen = 'http://127.0.0.1:5000'
    posts = list()
    try:
        posts = db.session.query(News, Category.name).join(Category).filter(News.title != None).filter(
            Category.name == category).order_by(News.date).all()
    except Exception as err:
        abort(404)
    else:
        news_list = list()
        news_lis = list()
        for post, category in posts:
            news_list.append({
                'title': post.title,
                'intro': post.intro,
                'text': post.text,
                'author': post.author,
                'img': f'{domen}/static{post.img}',
                'file_url': f'{domen}/static{post.file}',
                'date': post.date,
                'category': category
            })

        if len(news_list) == 0:
            abort(404)

    return jsonify({'news': news_list})


# Обработчик ошибок
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not Found!'}), 404
    else:
        return render_template('404.html'), 404