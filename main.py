from flask import Flask
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import xml.etree.ElementTree as XMLconfig
from flask_restful import reqparse

XMLtree = XMLconfig.parse('config.xml')
XMLroot = XMLtree.getroot()

dataBaseConfig = XMLroot.find('database')

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://{0}:{1}@{2}/{3}".format(dataBaseConfig.find('user').text,
 dataBaseConfig.find('password').text, dataBaseConfig.find('host').text, dataBaseConfig.find('name').text )

dataBase = SQLAlchemy(app)

class Serializable():
    def json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Users(dataBase.Model, Serializable):
    id = dataBase.Column("id", dataBase.Integer, primary_key=True)
    first_name = dataBase.Column("first_name", dataBase.String(100))
    last_name = dataBase.Column("last_name", dataBase.String(100))
    email = dataBase.Column("email", dataBase.String(100))

    def __init__(self, first_name, last_name, email):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='Id cannot be converted')
    parser.add_argument('first_name')
    parser.add_argument('last_name')
    parser.add_argument('email')

class UserRes(Resource):

    def post(self):
        return "post"

    def get(self):
        
        args = Users.parser.parse_args()

        if(args['id'] == None):
            users = Users.query.all()
            jusers = []
            for u in users:
                jusers.append(u.json())
            return jusers

        us = Users.query.filter_by(id=args['id']).first()

        if us:
            return us.json()
        else:
            return "prrrrt"

    def put(self):
        return "put"

    def patch(self):
        return "patch"

    def delete(self):
        return "delete"

api.add_resource(UserRes, '/user')

if __name__ == '__main__':
    dataBase.create_all()
    app.run(debug=True)