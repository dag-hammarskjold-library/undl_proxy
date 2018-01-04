#!  /usr/bin/env    python

## Utility script to create a NEW database.
## Do NOT use this if you do not want to clobber
## an existing DB

from sqlalchemy import create_engine
from flask import Flask
from config import DevelopmentConfig
from models import SearchMetadata

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

DB_URI = app.config.get('DB_URI', None)
engine = create_engine(DB_URI, convert_unicode=True)

SearchMetadata.metadata.create_all(bind=engine)
