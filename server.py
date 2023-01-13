from flask import Flask, jsonify, request
from flask.views import MethodView
from sqlalchemy import Column, Integer, String, DateTime, func, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.exc import IntegrityError
import atexit
import pydantic
from flask_bcrypt import Bcrypt
from typing import Optional

app = Flask('server')
bcrypt = Bcrypt(app)

DSN = 'postgresql://app:1234@127.0.0.1:5431/flask'
engine = create_engine(DSN)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def on_exit():
    engine.dispose()

atexit.register(on_exit)


# Error handler
class HttpError(Exception):

    def __init__(self, status_code: int, message: str or dict or list):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HttpError)
def http_error_handler(err: HttpError):
    response = jsonify({
        'status': 'error',
        'message': err.message
    })
    response.status_code = err.status_code
    return response


# Base classes
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(120), unique=True, nullable=False)
    password = Column(String, nullable=False)
    advertisements = relationship('Advertisement', backref='user')


class Advertisement(Base):
    __tablename__ = 'advertisement'

    id = Column(Integer, primary_key=True)
    headline = Column(String(60), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    owner_id = Column(Integer, ForeignKey('user.id'))


Base.metadata.create_all(engine)


class CreateUserSchema(pydantic.BaseModel):
    username: str
    password: str

    @pydantic.validator('password')
    def strong_password(cls, value: str):
        if len(value) <= 8:
            raise ValueError('password too short')
        return bcrypt.generate_password_hash(value.encode()).decode()


class CreateAdvSchema(pydantic.BaseModel):
    headline: str
    description: Optional[str]

    @pydantic.validator('headline')
    def good_headline(cls, value: str):
        if len(value) <= 10:
            raise ValueError('Describe your advertisement headline a bit better')
        return value


def validate(Schema, data: dict):
    try:
        data_validated = Schema(**data).dict(exclude_none=True)
    except pydantic.ValidationError as er:
        raise HttpError(400, er.errors())
    return data_validated


def get_user(user_id: int, session: Session) -> User:
    user = session.query(User).get(user_id)
    if user is None:
        raise HttpError(404, 'User not found')
    return user


def get_adv(adv_id: int, session: Session) -> Advertisement:
    advertisement = session.query(Advertisement).get(adv_id)
    if advertisement is None:
        raise HttpError(404, 'Advertisement not found')
    return advertisement


class UserView(MethodView):

    def get(self, user_id: int):
        with Session() as session:
            user = get_user(user_id, session)
            return jsonify({'username': user.username, 'advertisements': len(user.advertisements)})

    def post(self):
        json_data_validated = validate(CreateUserSchema, request.json)

        with Session() as session:
            new_user = User(username=json_data_validated['username'],
                            password=json_data_validated['password'])  # or use dict unpack if we are sure of structure - **json_data
            try:
                session.add(new_user)
                session.commit()
            except IntegrityError:
                raise HttpError(400, 'User already exists')
            return jsonify({'status': 'created', 'id': new_user.id})

    def delete(self, user_id: int):
        with Session() as session:
            user = get_user(user_id, session)
            session.delete(user)
            session.commit()
            return jsonify({'user_id': user_id, 'satus': 'deleted'})


class AdvertisementView(MethodView):

    def get(self, adv_id: int):
        with Session() as session:
            advertisement = get_adv(adv_id, session)
            return jsonify({'headline': advertisement.headline,
                        'description': advertisement.description,
                        'created_at': advertisement.created_at,
                        'owner_id': advertisement.owner_id,
                        })

    def post(self, user_id: int):
        json_data_validated = validate(CreateAdvSchema, request.json)

        with Session() as session:
            user = get_user(user_id, session)
            new_adv = Advertisement(headline=json_data_validated['headline'],
                                    description=json_data_validated['description'],
                                    owner_id=user.id)
            try:
                session.add(new_adv)
                session.commit()
            except:
                raise HttpError(400, 'Something wrong happened')
            return jsonify({'status': 'created', 'id': new_adv.id})

    def delete(self, adv_id: int):
        with Session() as session:
            advertisement = get_adv(adv_id, session)
            session.delete(advertisement)
            session.commit()
            return jsonify({'Adv_id': adv_id, 'satus': 'deleted'})


app.add_url_rule('/user/', methods=['POST'],
                 view_func=UserView.as_view('create_user'))
app.add_url_rule('/user/<int:user_id>', methods=['GET', 'DELETE'],
                 view_func=UserView.as_view('delete_user'))
app.add_url_rule('/user/<int:user_id>/adv/', methods=['POST'],
                 view_func=AdvertisementView.as_view('create_advertisement'))
app.add_url_rule('/adv/<int:adv_id>', methods=['GET', 'DELETE'],
                 view_func=AdvertisementView.as_view('get_delete_advertisement'))
app.run()
