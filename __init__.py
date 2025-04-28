# __init__.py ：初始化文件，创建Flask应用

from flask import Flask
from .exts import init_exts
from .views import init_admin_account, blue

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'abc123'
    app.register_blueprint(blueprint = blue)
    # 配置数据库
    # db_uri = 'sqlite:///sqlite3.db'  # sqlite配置
    db_uri = 'mysql+pymysql://root:123456@localhost:3306/flaskt'  # mysql的配置
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 禁止对象追踪修改

    # 初始化插件（写在配置数据库之后）
    init_exts(app=app)
    # 使用应用上下文
    with app.app_context():
        # 在应用上下文内初始化管理员账户
        init_admin_account()
    return app
