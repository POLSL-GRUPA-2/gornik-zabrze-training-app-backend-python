from flask import Flask, json, request, jsonify
from flask.helpers import make_response
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
import xml.etree.ElementTree as XMLconfig
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime

XMLtree = XMLconfig.parse('config.xml')
XMLroot = XMLtree.getroot()

dataBaseConfig = XMLroot.find('database')

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://{0}:{1}@{2}/{3}".format(dataBaseConfig.find('user').text,
 dataBaseConfig.find('password').text, dataBaseConfig.find('host').text, dataBaseConfig.find('name').text )
app.config['SECRET_KEY'] = "EEAAA"

dataBase = SQLAlchemy(app)

class Serializable():
    def json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Users(dataBase.Model, Serializable):
    id = dataBase.Column("id", dataBase.String(100), primary_key=True)
    first_name = dataBase.Column("first_name", dataBase.String(100))
    last_name = dataBase.Column("last_name", dataBase.String(100))
    email = dataBase.Column("email", dataBase.String(100))
    password_hash = dataBase.Column('password_hash', dataBase.String(64))

    def __init__(self, id, first_name, last_name, email, password_hash):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = password_hash

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

class Login(Resource):
    def get(self):
        
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

        user = Users.query.filter_by(email=auth.username).first()

        if not user:
            return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

        if check_password_hash(user.password_hash, auth.password):
            token = jwt.encode({'id' : user.id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'])

            return jsonify({'token' : token})
        
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

class Register(Resource):
    def post(self):
        data = request.get_json()

        #chceck if email already exists
        users_email = Users.query.filter_by(email=data['email']).first()
        if users_email:
            return jsonify({'message' : 'User with provided email address already exist!'})

        hashed_password = generate_password_hash(data['password'], method='sha256')

        new_user = Users(id=str(uuid.uuid1()), first_name=data['first_name'], last_name=data['last_name'], email=data['email'], password_hash=hashed_password)
        dataBase.session.add(new_user)
        dataBase.session.commit()

        return jsonify({'message' : 'User created successfully'})
        


api.add_resource(UserRes, '/user')
api.add_resource(Login, '/login')
api.add_resource(Register, '/register')

if __name__ == '__main__':
    dataBase.create_all()
    app.run(debug=True)