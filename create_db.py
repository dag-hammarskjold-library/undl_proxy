#!  /usr/bin/env    python

# Utility script to create a NEW database.
# Do NOT use this if you do not want to clobber
# an existing DB

from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists
from flask import Flask
from undl_proxy.config import DevelopmentConfig
from undl_proxy.models import SearchMetadata

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

DB_URI = app.config.get('DB_URI', None)
engine = create_engine(DB_URI, convert_unicode=True)

if not database_exists(DB_URI):
    SearchMetadata.metadata.create_all(bind=engine)
    print("Created new database '{}'".format(app.config.get("POSTGRES_DB")))
else:
    print("Database '{}'' already exists".format(app.config.get("POSTGRES_DB")))
