from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask import Flask
from .config import DevelopmentConfig
from .models import SearchMetadata

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

DB_URI = app.config.get('DB_URI', None)
engine = create_engine(DB_URI, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def connection():
    connection = engine.connect()
    return connection


def get_session():
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    SearchMetadata.metadata.create_all(bind=engine)
