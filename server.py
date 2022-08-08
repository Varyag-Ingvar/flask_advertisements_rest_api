from __future__ import annotations

import pydantic
import typing
from flask import Flask, jsonify, request
from flask.views import MethodView
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, func, create_engine


class HttpError(Exception):
    """class for process some errors"""

    def __init__(self, status_code: int, message: str | dict | list):
        self.status_code = status_code
        self.message = message


class CreateAd(pydantic.BaseModel):
    ad_name: str
    ad_body: str
    ad_owner: str


class PatchAd(pydantic.BaseModel):
    ad_name: typing.Optional[str]
    ad_body: typing.Optional[str]
    ad_owner: typing.Optional[str]


def validate(model, raw_data: dict):
    try:
        return model(**raw_data).dict()
    except pydantic.ValidationError as error:
        raise HttpError(400, error.errors())


app = Flask('app')


@app.errorhandler(HttpError)
def http_error_handler(error: HttpError):
    """function that processes errors"""
    response = jsonify({
        'status': 'error',
        'reason': error.message
    })
    response.status_code = error.status_code
    return response


PG_DSN = 'postgresql://app:1234@127.0.0.1/advertisements_db'

engine = create_engine(PG_DSN)
Base = declarative_base()
Session = sessionmaker(bind=engine)  # connection to the database


class Advertisement(Base):
    __tablename__ = 'advertisements'
    id = Column(Integer, primary_key=True)
    ad_name = Column(String, index=True, unique=True, nullable=False)
    ad_body = Column(String, nullable=False)
    ad_owner = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


def get_ad(session: Session, ad_id: int):
    ad = session.query(Advertisement).get(ad_id)
    if ad is None:
        raise HttpError(404, 'advertisement not found')
    return ad


Base.metadata.create_all(engine)   # created db tables migrations


class AdView(MethodView):

    def get(self, ad_id: int):
        with Session() as session:
            ad = get_ad(session, ad_id)
            return jsonify({'ad_name': ad.ad_name, 'ad_body': ad.ad_body, 'ad_owner': ad.ad_owner,
                            'created_at': ad.created_at.isoformat()})

    def post(self):
        validated = validate(CreateAd, request.json)
        with Session() as session:
            ad = Advertisement(ad_name=validated['ad_name'], ad_body=validated['ad_body'],
                               ad_owner=validated['ad_owner'])
            session.add(ad)
            session.commit()  # create object in database
            return {'id': ad.id, 'ad_name': ad.ad_name}

    def patch(self, ad_id):
        validated = validate(PatchAd, request.json)
        with Session() as session:
            ad = get_ad(session, ad_id)
            if validated.get('ad_name'):
                ad.ad_name = validated['ad_name']
            if validated.get('ad_body'):
                ad.ad_body = validated['ad_body']
            session.add(ad)
            session.commit()
            return {
                'status': 'success'
            }

    def delete(self, ad_id: int):
        with Session() as session:
            ad = get_ad(session, ad_id)
            session.delete(ad)
            session.commit()
            return {
                'status': 'success'
            }


ad_view = AdView.as_view('ads')
app.add_url_rule('/ads/', view_func=ad_view, methods=['POST'])
app.add_url_rule('/ads/<int:ad_id>', view_func=ad_view, methods=['GET', 'PATCH', 'DELETE'])


app.run()


