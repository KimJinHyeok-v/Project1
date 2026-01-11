from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

import config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # DB + Migrate
    db.init_app(app)
    migrate.init_app(app, db)

    # 모델 로딩
    from . import models

    # Blueprint 등록
    from .views import (
        main_views,
        auth_views,
        question_views,
        answer_views,
        data_views,
        predict_views,
        ai_views,
        ai_tools_views,
        ai2_views,
        center_api_views,
        ai2_chat_views
    )

    app.register_blueprint(main_views.bp)
    app.register_blueprint(auth_views.bp)
    app.register_blueprint(question_views.bp)
    app.register_blueprint(answer_views.bp)
    app.register_blueprint(data_views.bp)
    app.register_blueprint(predict_views.bp)
    app.register_blueprint(ai_views.bp)
    app.register_blueprint(ai_tools_views.bp)
    app.register_blueprint(ai2_views.bp)
    app.register_blueprint(center_api_views.bp)
    app.register_blueprint(ai2_chat_views.bp)
    return app