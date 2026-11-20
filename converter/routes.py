from flask import Blueprint, jsonify, render_template
from sqlalchemy import text

from converter import db

api = Blueprint("api", __name__)


@api.get("/")
def index():
    return render_template("index.html")


@api.get("/api/health")
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify(status="ok")
