import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime
import hashlib

Base = declarative_base()


class DocumentMetadata(Base):
    __tablename__ = 'document_metadata'

    id = Column(Integer, primary_key=True)
    document_symbol = Column(String, unique=True)
    metadata_json = Column(Text)
    metadata_hash = Column(String)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime, onupdate=datetime.datetime)

    def _set_hash(self):
        m = hashlib.sha256()
        m.update(repr(self.metadata_json).encode('UTF-8'))
        return m.hexdigest()

    def __init__(self, document_symbol, metadata_json):
        self.metadata_json = metadata_json
        self.document_symbol = document_symbol
        self.metadata_hash = self._set_hash()

    def __repr__(self):
        return "<DocumentMetadata: {}".format(self.document_symbol)
