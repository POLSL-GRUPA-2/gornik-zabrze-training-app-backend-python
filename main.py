from flask import Flask
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import pymysql
import xml.etree.ElementTree as XMLconfig
import json

XMLtree = XMLconfig.parse('config.xml')
XMLroot = XMLtree.getroot()

dataBaseConfig = XMLroot.find('database')

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://{0}:{1}@{2}/{3}".format(dataBaseConfig.find('user').text,
 dataBaseConfig.find('password').text, dataBaseConfig.find('host').text, dataBaseConfig.find('name').text )

dataBase = SQLAlchemy(app)

class Serializable():
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Users(dataBase.Model, Serializable):
    id = dataBase.Column("id", dataBase.Integer, primary_key=True)
    firstname = dataBase.Column("firstname", dataBase.String(100))
    lastname = dataBase.Column("lastname", dataBase.String(100))
    email = dataBase.Column("email", dataBase.String(100))

    def __init__(self, firstname, lastname, email):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email


class HelloWorld(Resource):
    def get(self):
        
        print("aaaa")
        us = Users.query.filter_by(firstname="Andrzej").first()

        if us:
            return us.as_dict()
        else:
            return "prrrrt"

api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
    dataBase.create_all()
    app.run(debug=True)