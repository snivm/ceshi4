from .exts import db
import datetime


class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(80), primary_key = True)
    password = db.Column(db.String(80))
    usertype = db.Column(db.String(80))


class LoginLog(db.Model):
    __tablename__ = 'login_logs'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80))
    ip_address = db.Column(db.String(20))
    login_time = db.Column(db.DateTime)


class AIPhoto(db.Model):
    __tablename__ = 'ai_photo'
    id = db.Column(db.Integer, primary_key = True)
    userid = db.Column(db.String(80))
    username = db.Column(db.String(80))
    fileanme = db.Column(db.String(255))
    login_time = db.Column(db.DateTime)
    result = db.Column(db.String(255))
    con_level = db.Column(db.Float)

    def __repr__(self):
        return self.name