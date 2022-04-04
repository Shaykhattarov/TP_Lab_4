import hashlib, uuid

from datetime import datetime as dt
from flask_login import UserMixin
from app import db


class User(db.Model, UserMixin):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(300), nullable=False)
    user_surname = db.Column(db.String(300), nullable=False)
    user_email = db.Column(db.String(2025), nullable=False)
    user_password = db.Column(db.String, nullable=False)
    user_old = db.Column(db.Integer, nullable=False)
    user_work = db.Column(db.String(300))
    user_img = db.Column(db.String(2025))

    def __repr__(self):
        return f'<user {self.user_id}> '

    def get_id(self):
        return self.user_id

    @staticmethod
    def hash_password(password):
        salt = uuid.uuid4().hex
        return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

    @staticmethod
    def check_password(hashed_password, user_password):
        password, salt = hashed_password.split(':')
        return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()


class News(db.Model, UserMixin):
    __tablename__ = "news"
    news_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    news_title = db.Column(db.String(255), nullable=True)
    news_intro = db.Column(db.String(300), nullable=True)
    news_text = db.Column(db.Text, nullable=True)
    news_author = db.Column(db.String(300), nullable=True)
    news_img = db.Column(db.String(2049), nullable=True)
    news_date = db.Column(db.DateTime, default=dt.utcnow())

    def __repr__(self):
        return f'<news {self.news_id}>'

