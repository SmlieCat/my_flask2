from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)


app.debug = True

#对cook进行加密, os.urandom作为随机数发生器
app.secret_key = os.urandom(24)

#根目录
APPS_DIR = os.path.dirname(__file__)
#静态目录
STATIC_DIR = os.path.join(APPS_DIR, 'static')
#数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123qwerty@127.0.0.1:3306/flask_blog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)





#切记循环引用问题
import apps.views