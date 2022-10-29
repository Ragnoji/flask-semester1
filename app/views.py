from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request,
    session, url_for
)

from app.db import get_db


bp = Blueprint('views', __name__)


@bp.route('/')
def index():
    render_template('products/index.html')