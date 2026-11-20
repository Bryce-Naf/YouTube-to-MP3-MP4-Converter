import os

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import RequestEntityTooLarge

db = SQLAlchemy()

MAX_UPLOAD_BYTES = 500 * 1024 * 1024


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///app.sqlite"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_UPLOAD_BYTES=MAX_UPLOAD_BYTES,
        MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES + 1024 * 1024,
        MEDIA_STORAGE_PATH=os.path.join(app.instance_path, "media_jobs"),
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    from converter.routes import api

    app.register_blueprint(api)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_upload_too_large(error):
        return (
            jsonify(error=f"{error.name}: upload exceeds the 500 MB file size limit."),
            413,
        )

    with app.app_context():
        db.create_all()

    return app
