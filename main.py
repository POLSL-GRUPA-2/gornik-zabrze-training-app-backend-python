from datetime import timedelta
from flask import Flask
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import pymysql
import xml.etree.ElementTree as XMLconfig

XMLtree = XMLconfig.parse('config.xml')
XMLroot = XMLtree.getroot()

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = XMLroot.find('database_string').text

dataBase = SQLAlchemy(app)

class Users(dataBase.Model):
    id = dataBase.Column("id", dataBase.Integer, primary_key=True)
    fistName = dataBase.Column("firstname", dataBase.String(100))
    lastName = dataBase.Column("lastname", dataBase.String(100))
    email = dataBase.Column("email", dataBase.String(100))

    def __init__(self, firstName, lastName, email):
        self.fistName = firstName
        self.lastName = lastName
        self.email = email



class HelloWorld(Resource):
    def get(self):

        us = Users.query.filter_by(fistName="Jakub").first()

        if us:
            return us.lastName
        else:
            return "prrrrt"

api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
    dataBase.create_all()
    app.run(debug=True)