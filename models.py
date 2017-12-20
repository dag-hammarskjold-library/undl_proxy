import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, String, DateTime

Base = declarative_base()


class SearchMetadata(Base):
    __tablename__ = 'search_metadata'

    id = Column(Integer, primary_key=True)
    undl_url = Column(String, unique=True)
    xml = Column(Text, nullable=True)
    json = Column(Text, nullable=True)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)

    def __init__(self, undl_url):
        self.undl_url = undl_url

    def __repr__(self):
        return "<DocumentMetadata: {}".format(self.undl_url)

    def to_dict(self):
        if self.updated:
            return {
                "id": self.id,
                "url": self.undl_url,
                "xml": self.xml,
                "json": self.json,
                "created": self.created.strftime("%x %X"),
                "updated": self.updated.strftime("%x %X")
            }
        else:
            return {
                "id": self.id,
                "url": self.undl_url,
                "xml": self.xml,
                "json": self.json,
                "created": self.created.strftime("%x %X")
            }
