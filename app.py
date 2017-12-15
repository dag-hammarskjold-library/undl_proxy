from flask import Flask, render_template, request
from logging import getLogger
from sqlalchemy.exc import SQLAlchemyError
import json
from .models import DocumentMetadata
from .db import db_session
from .base_page import BasePage
from .config import DevelopmentConfig

app = Flask(__name__)
logger = getLogger(__name__)

app.config.from_object(DevelopmentConfig)


def session_commit(session, msg):
    session.flush()
    try:
        session.commit()
    except SQLAlchemyError as e:
        print("Caught Commit error in {}: {}".format(msg, e))
        session.rollback()


@app.errorhandler(404)
def page_not_found(e):
    app.logger.error(e)
    return render_template('404.html'), 404


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        pass
    elif request.method == 'GET':
        return render_template('index.html')


def _fetch_metadata(document_symbol):
    metadata_url = app.config.get("METADATA_URL")
    page = BasePage()
    root = page.get_root(metadata_url + '?doc_symbol={}'.format(document_symbol))
    metadata_json = root.xpath('.//pre[@id="document-metadata"]/text()')
    return metadata_json[0]
