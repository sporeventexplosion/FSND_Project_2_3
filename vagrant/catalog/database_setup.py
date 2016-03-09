from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String(250), nullable=False, unique=True)
    name = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)

    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(User)


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(400))

    category_id = Column(Integer, ForeignKey("category.id"))
    category = relationship(Category)

    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(User)


# Connect to database and create tables. Leave at end of file
engine = create_engine("sqlite:///catalog.db")

Base.metadata.create_all(engine)
