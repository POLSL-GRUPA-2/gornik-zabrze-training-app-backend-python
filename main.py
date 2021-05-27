from flask import Flask, json, request, jsonify
from flask.helpers import make_response
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
import xml.etree.ElementTree as XMLconfig
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from flask_cors import CORS
import os


#CONFIGURATION

app = Flask(__name__)
api = Api(app)
CORS(app, supports_credentials=True)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://sql11415331:XVAaPJQ7If@sql11.freemysqlhosting.net:3306/sql11415331"
app.config['SECRET_KEY'] = "EEAAA"

dataBase = SQLAlchemy(app)

class Serializable():
    def json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

#MODELS

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

#DECORATORS

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'token' in request.cookies:
            token = request.cookies['token']

        if not token:
            return jsonify({'message' : 'Token is missing'})

        try:
            token_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS512", "HS256"])
            current_user = Users.query.filter_by(id=token_data['id']).first()
        except:
            return jsonify({'message' : 'Token is invalid!'})

        return f(current_user, *args, **kwargs)
    return decorated    

#RESOURCES

class Dupa(Resource):
    def get(self):
        return "spierdlaj"

class UsersCRUD(Resource):

    def post(self):
        return "post"

    @token_required
    def get(current_user, self):
        
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
    def post(self):
        
        auth = request.get_json()
        if not auth or not auth['email'] or not auth['password']:
            return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

        user = Users.query.filter_by(email=auth['email']).first()

        if not user:
            return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

        if check_password_hash(user.password_hash, auth['password']):
            token = jwt.encode({'id' : user.id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm="HS512")

            response = make_response({'Message' : 'Login successfull'})
            response.set_cookie('token', token, httponly = True, secure=True)
            return response
        
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

class Register(Resource):
    def post(self):
        data = request.get_json()

        #chceck if email already exists
        users_email = Users.query.filter_by(email=data['email']).first()
        if users_email:
            return jsonify({'message' : 'User with provided email address already exist!'})

        hashed_password = generate_password_hash(data['password'], method='sha256')

        new_user = Users(id=str(uuid.uuid4()), first_name=data['first_name'], last_name=data['last_name'], email=data['email'], password_hash=hashed_password)
        dataBase.session.add(new_user)
        dataBase.session.commit()

        return jsonify({'message' : 'User created successfully'})
        
class Logout(Resource):
    def get(self):
        response = make_response({'Message' : 'Logout successfull'})
        response.set_cookie('token', '', expires=0)
        return response

class Account(Resource):
    @token_required
    def get(current_user, self):
        return current_user.json()


api.add_resource(UsersCRUD, '/user')
api.add_resource(Login, '/login')
api.add_resource(Register, '/register')
api.add_resource(Logout, '/logout')
api.add_resource(Account, '/account')
api.add_resource(Dupa, '/')

def main(*args, **kwargs):
    dataBase.create_all()
    #port = int(os.environ.get('PORT', 5000))
    app.run(debug=True)

