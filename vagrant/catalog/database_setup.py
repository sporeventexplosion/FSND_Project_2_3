from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orgm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


# Connect to database and create tables. Leave at end of file
engine = create_engine("sqlite:///catalog.db")

Base.metadata.create_all(engine)
