from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):

    """ A user entry used to identify users of the app """

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String(250), nullable=False, unique=True)
    name = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):

    """ A category in the app belonging to a give user """

    __tablename__ = "category"

    @property
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp
        }

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    # Use an int for timestamp to work around some SQLite limitations
    # Not used at the moment
    timestamp = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(User)


class Item(Base):

    """ An item in the app in a given category and belonging to a user """

    __tablename__ = "item"

    @property
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "timestamp": self.timestamp,
            "category_id": self.category_id
        }

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(400))
    timestamp = Column(Integer, nullable=False)

    category_id = Column(Integer, ForeignKey("category.id"))
    category = relationship(Category)

    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(User)


# Connect to database and create tables. Leave at end of file
engine = create_engine("sqlite:///catalog.db")

Base.metadata.create_all(engine)
