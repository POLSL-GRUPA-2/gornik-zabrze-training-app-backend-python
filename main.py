from flask import Flask, request, jsonify
from flask.helpers import make_response
from flask_restful import Resource, Api, reqparse
from flask import Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import uuid
from sqlalchemy.sql.functions import user
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
api = Api(app)
CORS(app, supports_credentials=True)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://sql11437697:eURCctBUti@sql11.freemysqlhosting.net:3306/sql11437697"
app.config['SECRET_KEY'] = "EEAAA"

dataBase = SQLAlchemy(app)

def serialize_list(list):
    json_list = []
    for l in list:
        json_list.append(l.json())
    return json_list

class Serializable():
    def json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

#MODELS#

class Users(dataBase.Model, Serializable):
    __tablename__='Users'
    id = dataBase.Column("id", dataBase.String(100), primary_key=True)
    first_name = dataBase.Column("first_name", dataBase.String(100))
    last_name = dataBase.Column("last_name", dataBase.String(100))
    email = dataBase.Column("email", dataBase.String(100))
    password_hash = dataBase.Column('password_hash', dataBase.String(64))
    role_id = dataBase.Column('role',dataBase.Integer, dataBase.ForeignKey('Roles.id'), nullable=False)


    player = dataBase.relationship('Players', backref='user', lazy=True)
    coach = dataBase.relationship('Coaches', backref='user', lazy=True)
    messages_sent = dataBase.relationship('Messages', backref='sender', foreign_keys='Messages.sender_id', lazy=True)
    messages_recieved = dataBase.relationship('Messages', backref='reciever', foreign_keys='Messages.reciever_id', lazy=True)
    team_message_sent = dataBase.relationship('TeamMessages', backref='sender', foreign_keys='TeamMessages.sender_id', lazy=True)

    def __init__(self, id, first_name, last_name, email, password_hash, role_id):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = password_hash
        self.role_id = role_id

    def json(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'role': self.role_id
        }

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int, help='Id cannot be converted')
    parser.add_argument('first_name')
    parser.add_argument('last_name')
    parser.add_argument('email')

class Coaches(dataBase.Model, Serializable):
    __tablename__='Coaches'
    id = dataBase.Column("id", dataBase.Integer, primary_key=True)
    user_id = dataBase.Column("user_id", dataBase.String(255), dataBase.ForeignKey('Users.id'), nullable=False)
    teams = dataBase.relationship('Teams', backref='coach', lazy=True)

    def __init__(self, id, user_id):
        self.id = id
        self.user_id = user_id


    parser = reqparse.RequestParser()
    parser.add_argument('id')
    parser.add_argument('user_id')

class TeamsPlayersAssociations(dataBase.Model):
    __tablename__ = 'TeamsPlayersAssociations'
    team_id = dataBase.Column('team_id', dataBase.Integer, dataBase.ForeignKey('Teams.id'), primary_key=True)
    player_id = dataBase.Column('player_id', dataBase.Integer, dataBase.ForeignKey('Players.id'), primary_key=True)
    role = dataBase.Column('role', dataBase.Integer)

    team = dataBase.relationship("Teams", back_populates="players")
    player = dataBase.relationship("Players", back_populates="teams")


    def __init__(self, team_id, player_id, role):
        self.team_id = team_id
        self.player_id = player_id
        self.role = role

class Roles(dataBase.Model):
    __tablename__='Roles'
    id = dataBase.Column('id', dataBase.Integer, primary_key=True)
    role_name = dataBase.Column('role_name', dataBase.String(255))
    users = dataBase.relationship('Users', backref='role', lazy=True)

class Teams(dataBase.Model, Serializable):
    __tablename__='Teams'
    id = dataBase.Column("id", dataBase.Integer, primary_key=True)
    team_name = dataBase.Column('team_name', dataBase.String(255))
    coach_id = dataBase.Column("coach_id", dataBase.Integer, dataBase.ForeignKey('Coaches.id'), nullable=False)
    players = dataBase.relationship('TeamsPlayersAssociations', back_populates='team')
    tasks = dataBase.relationship('TeamTasks', backref='team', lazy=True)


    def __init__(self, id, team_name, coach_id):
        self.id = id
        self.team_name = team_name
        self.coach_id = coach_id

    parser = reqparse.RequestParser()
    parser.add_argument('id')
    parser.add_argument('coach_id')
    parser.add_argument('player_id')

class Players(dataBase.Model, Serializable):
    __tablename__='Players'
    id = dataBase.Column("id", dataBase.Integer, primary_key=True)
    user_id = dataBase.Column("user_id", dataBase.String(255), dataBase.ForeignKey('Users.id'), nullable=False) 
    teams = dataBase.relationship('TeamsPlayersAssociations', back_populates='player')
    tasks = dataBase.relationship('PersonalTasks', backref='player', lazy=True)

    def __init__(self, id, user_id, teams):
        self.id = id
        self.teams = teams
        self.user_id = user_id

    def json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
        }
    parser = reqparse.RequestParser()
    parser.add_argument('id')
    parser.add_argument('team_id')
    parser.add_argument('user_id')

class PersonalTasks(dataBase.Model, Serializable):
    __tablename__ = 'PersonalTasks'
    id = dataBase.Column('id', dataBase.Integer, primary_key=True)
    task_date = dataBase.Column('task_date', dataBase.Date)
    coach_id = dataBase.Column('coach_id', dataBase.Integer, dataBase.ForeignKey('Coaches.id'), nullable=False)
    player_id = dataBase.Column('player_id', dataBase.Integer, dataBase.ForeignKey('Players.id'), nullable=False)
    description = dataBase.Column('description', dataBase.String(255))
    done = dataBase.Column('done', dataBase.Boolean)

    def __init__(self, id, task_date, coach_id, player_id, description, done) -> None:
        self.id = id
        self.task_date = task_date
        self.coach_id = coach_id
        self.player_id = player_id
        self.description = description
        self.done = done

    def json(self):
        return {
            'id': self.id,
            'task_date': str(self.task_date),
            'coach_id': self.coach_id,
            'player_id': self.player_id,
            'description': self.description,
            'done': self.done
        }

    parser = reqparse.RequestParser()
    parser.add_argument('id')
    parser.add_argument('task_date')
    parser.add_argument('coach_id')
    parser.add_argument('user_id')
    parser.add_argument('done')

class TeamTasks(dataBase.Model, Serializable):
    __tablename__ = 'TeamTasks'
    id = dataBase.Column('id', dataBase.Integer, primary_key=True)
    task_date = dataBase.Column('task_date', dataBase.Date)
    team_id = dataBase.Column('team_id', dataBase.Integer, dataBase.ForeignKey('Teams.id'), nullable=False)
    description = dataBase.Column('description', dataBase.String(255))
    done = dataBase.Column('done', dataBase.Boolean)

    def __init__(self, id, task_date, team_id, description, done) -> None:
        self.id = id
        self.task_date = task_date
        self.team_id = team_id
        self.description = description
        self.done = done

    def json(self):
        return {
            'id': self.id,
            'task_date': str(self.task_date),
            'team_id': self.team_id,
            'description': self.description,
            'done': self.done
        }

    parser = reqparse.RequestParser()
    parser.add_argument('id')
    parser.add_argument('task_date')
    parser.add_argument('user_id')
    parser.add_argument('done')

class Messages(dataBase.Model, Serializable):
    __tablename__ = 'Messages'
    id = dataBase.Column('id', dataBase.Integer, primary_key=True)
    reciever_id = dataBase.Column('reciever_id', dataBase.String(255), dataBase.ForeignKey('Users.id'), nullable=False)
    sender_id = dataBase.Column('sender_id', dataBase.String(255), dataBase.ForeignKey('Users.id'), nullable=False)
    message = dataBase.Column('message', dataBase.String(2048), nullable=False)
    time_stamp = dataBase.Column('time_stamp', dataBase.DateTime, nullable=False)

    def __init__(self, id, reciever_id, sender_id, message, time_stamp) -> None:
        self.id = id
        self.reciever_id = reciever_id
        self.sender_id = sender_id
        self.message = message
        self.time_stamp = time_stamp


    def json(self):
        return {
            'id': self.id,
            'reciever_id': self.reciever_id,
            'sender_id': self.sender_id,
            'message': self.message,
            'time_stamp': str(self.time_stamp)
        }
    
    parser = reqparse.RequestParser()
    parser.add_argument('id')
    parser.add_argument('reciever_id')
    parser.add_argument('sender_id')
    parser.add_argument('time_stamp')

class TeamMessages(dataBase.Model, Serializable):
    __tablename__ = 'TeamMessages'
    id = dataBase.Column('id', dataBase.Integer, primary_key=True)
    team_id = dataBase.Column('team_id', dataBase.Integer, dataBase.ForeignKey('Teams.id'), nullable=False)
    sender_id = dataBase.Column('sender_id', dataBase.String(255), dataBase.ForeignKey('Users.id'), nullable=False)
    message = dataBase.Column('message', dataBase.String(2048), nullable=False)
    time_stamp = dataBase.Column('time_stamp', dataBase.DateTime, nullable=False)

    def __init__(self, id, team_id, sender_id, message, time_stamp) -> None:
        self.id = id
        self.team_id = team_id
        self.sender_id = sender_id
        self.message = message
        self.time_stamp = time_stamp


    def json(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'sender_id': self.sender_id,
            'message': self.message,
            'time_stamp': str(self.time_stamp)
        }

    parser = reqparse.RequestParser()
    parser.add_argument('id')
    parser.add_argument('team_id')
    parser.add_argument('sender_id')
    parser.add_argument('time_stamp')

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

class UsersCRUD(Resource):

    @token_required
    def get(current_user, self):
        user_id = request.args.get('user_id')
        team_id = request.args.get('team_id')
        coach_id = request.args.get('coach_id')
        player_id = request.args.get('player_id')

        if user_id is not None:
            user = Users.query.filter_by(id=user_id).first()
            return user.json()
        elif team_id is not None:
            users = Users.query.join(Users.player).join(Players.teams).filter_by(team_id=team_id).all()
            return serialize_list(users)  
        elif coach_id is not None:
            user = Users.query.join(Users.coach).filter_by(id=coach_id).first()
            return user.json()
        elif player_id is not None:
            user = Users.query.join(Users.player).filter_by(id=player_id).first()
            return user.json()
        else:
            users = Users.query.all()
            return serialize_list(users)

    @token_required
    def patch(current_user, self):
        data = request.json

        user = Users.query.filter_by(id=data['id']).first()
        if current_user.id == user.id or current_user.role.id == 3:
            if data['first_name'] is not None:
                user.first_name = data['first_name']
            if data['last_name'] is not None:    
                user.last_name = data['last_name']
            if 'password' in data:
                if data['password'] != '' and data['password'] is not None:
                    password_hash = generate_password_hash(data['password'], method='sha256')
                    user.password_hash = password_hash

            if data['email'] is not None:
                user.email = data['email']

        if current_user.role_id == 3:
            if 'role' in data:
                user.role_id = data['role']

        dataBase.session.commit()

        return jsonify({'message' : 'User succesfully updated'}) 

class TeamCRUD(Resource):

    @token_required
    def post(current_user, self):
        if current_user.role_id >= 2:
            data = request.get_json()
            team_name = data['team_name']

            new_team = Teams(id=None, team_name=team_name, coach_id=None)
            dataBase.session.add(new_team)
            dataBase.session.commit()

            return jsonify({'message' : 'Team created succesfully'})
        else:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json')
    
    @token_required
    def get(current_user, self):
        user_id = request.args.get('user_id')
        player_id = request.args.get("player_id")
        coach_id = request.args.get('coach_id')
        if player_id is not None:
            teams = Teams.query.join(Teams.players).filter_by(player_id=player_id).all()
            return serialize_list(teams)
        if user_id is not None:
            teams = Teams.query.join(Teams.players).join(Players.user).filter_by(id=user_id).all()
            teams += Teams.query.join(Teams.coach).join(Coaches.user).filter_by(id=user_id).all()
            return serialize_list(teams)
        elif coach_id is not None:
            teams = Teams.query.filter_by(coach_id=coach_id).all()
            return serialize_list(teams)
        else:
            teams = Teams.query.all()
            return serialize_list(teams)      

    @token_required
    def patch(current_user, self):
        if current_user.role_id >= 2:
            data = request.get_json()
            team_id = data['team_id']
            team_name = data['team_name']
            user_id = data['user_id']

            team = Teams.query.filter_by(id=team_id).first()

            if team:
                team.team_name = team_name

                coach = Coaches.query.filter_by(user_id = user_id).first()

                team.coach_id = coach.id
                dataBase.session.commit()
                return jsonify({'message' : 'Team updated succesfully'}) 
            else:
                return Response("{'message':'No team with such team_id found'}", status=500, mimetype='application/json')  
        else:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json')  


    def delete(self):
        return "delete"

class CoachCRUD(Resource):

    @token_required
    def post(current_user, self):
        if current_user.role_id >= 2:
            data = request.get_json()
            user_id = data['user_id']

            query = Coaches.query.filter_by(user_id=user_id).first()
            if not query:
                user = Users.query.filter_by(id=user_id).first()
                if user:
                    user.role_id = 2
                    new_coach = Coaches(id = None, user_id=user_id)
                    dataBase.session.add(new_coach)
                    dataBase.session.commit()
                    return jsonify({'message' : 'User promoted to coach'})  
                else:
                    return Response("{'message':'No user with such user_id found'}", status=500, mimetype='application/json')  
            else:
                return Response("{'message':'User is allready a coach'}", status=200, mimetype='application/json')  
        else:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json') 

    @token_required
    def get(current_user, self):
        user_id = request.args.get('user_id')
        
        if user_id is not None:
            coach = Coaches.query.filter_by(user_id=user_id).first()
            return coach.json()

    @token_required
    def delete(current_user, self):
        if current_user.role_id >= 2:
            user_id = request.args.get('user_id')
            coach_id = request.args.get('coach_id')

            if user_id is not None:
                coach = Coaches.query.filter_by(user_id=user_id).first()
                user = Users.query.filter_by(id = user_id).first()
            elif coach_id is not None:
                coach = Coaches.query.filter_by(id=coach_id).first()
                user = Users.quert.filter_by(id = coach.user_id).first()
            else:
                coach = None

            if coach:
                teams = Teams.query.filter_by(coach_id = coach.id).all()
                user.role_id = 1
                for t in teams:
                    teams.coach_id = None
                query = Coaches.query.filter_by(id=coach.id)
                query.delete()
                dataBase.session.commit()
                return jsonify({'message' : 'Coach deleted'})             
            else:
                return Response("{'message':'Coach not found'}", status=500, mimetype='application/json')
        else:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json')           

class PlayerCRUD(Resource):

    @token_required
    def post(current_user, self):
        if current_user.role_id >= 2:
            data = request.get_json()
            user_id = data['user_id']

            query = Players.query.filter_by(user_id=user_id).first()
            if not query:
                if user:
                    new_coach = Players(id = None, user_id=user_id, teams=[])
                    dataBase.session.add(new_coach)
                    dataBase.session.commit()
                    return jsonify({'message' : 'User promoted to player'})  
                else:
                    return Response("{'message':'User is allready a player'}", status=500, mimetype='application/json')
            else:
                return Response("{'message':'User is allready a player'}", status=200, mimetype='application/json')
        else:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json') 

    @token_required
    def get(current_user, self):
        user_id = request.args.get('user_id')
        team_id = request.args.get('team_id')

        if user_id is not None:
            player = Players.query.filter_by(user_id=user_id).first()
            if player:
                return player.json()
            else:
                return Response("{'message':'Player with such user_id doesn\'t exist'}", status=500, mimetype='application/json')
        elif team_id is not None:
            players = Players.query.join(Players.teams).filter_by(team_id=team_id).all()
            return serialize_list(players)

    @token_required
    def delete(current_user, self):
        if current_user.role_id < 2:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json')
        player_id = request.args.get('player_id')

        player = Players.query.filter_by(id=player_id)
        if player.first():
            player.delete()
            dataBase.session.commit()
            return jsonify({'message':'Player succesfully deleted'})
        else:
            return Response("{'message':'No player with such id exists'}", status=500, mimetype='application/json')

class PersonalTasksCRUD(Resource):
    @token_required
    def post(current_user, self):
        if current_user.role_id < 2:
            return jsonify({'message' : 'Access denied'}) 
        data = request.get_json()
        date = datetime.strptime(data['task_date'], '%Y-%m-%d %H:%M:%S')

        new_task = PersonalTasks(id=None, task_date=date, coach_id=data['coach_id'], player_id=data['player_id'], description=data['description'], done=False)
        dataBase.session.add(new_task)
        dataBase.session.commit()
        return jsonify({'message' : 'Task succesfully added'})  

    @token_required
    def get(current_user, self):
        task_id = request.args.get('task_id')
        task_date = request.args.get('task_date')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        player_id = request.args.get('player_id')
        coach_id = request.args.get('coach_id')

        if task_id is not None:
            personal_tasks = PersonalTasks.query.filter(PersonalTasks.id == task_id).all()
            return personal_tasks.json()

        if start_date is not None and end_date is not None and player_id is not None:

            start = datetime.strptime(start_date, '%Y-%m-%d-%H:%M:%S')
            end = datetime.strptime(end_date, '%Y-%m-%d-%H:%M:%S')
            personal_tasks = PersonalTasks.query.filter(PersonalTasks.task_date >= start, PersonalTasks.task_date <= end, PersonalTasks.player_id == player_id).all()
            return serialize_list(personal_tasks)
            
        if task_date is not None and player_id is not None:
            date = datetime.strptime(task_date, '%Y-%m-%d-%H:%M:%S')
            personal_tasks = PersonalTasks.query.filter(PersonalTasks.task_date == date, PersonalTasks.player_id == player_id).all()
            return serialize_list(personal_tasks)

        if task_date is not None:
            date = datetime.strptime(task_date, '%Y-%m-%d-%H:%M:%S')
            personal_tasks = PersonalTasks.query.filter(PersonalTasks.task_date == date).all()
            return serialize_list(personal_tasks)
        
        if player_id is not None:
            personal_tasks = PersonalTasks.query.filter(PersonalTasks.player_id == player_id).all()
            return serialize_list(personal_tasks)

        if coach_id is not None:
            personal_tasks = PersonalTasks.query.filter(PersonalTasks.coach_id == coach_id).all()
            return serialize_list(personal_tasks)

    @token_required
    def patch(current_user, self):

        data = request.get_json()

        task = PersonalTasks.query.filter_by(id=data['id']).first()
        if current_user.role.id >=  2:
            task.task_date = datetime.strptime(data['task_date'], '%Y-%m-%d-%H:%M:%S')
            task.coach_id = data['coach_id']
            task.player_id = data['player_id']
            task.description = data['description']
        task.done = data['done']

        dataBase.session.commit()

        return jsonify({'message' : 'Task succesfully updated'})  

    @token_required
    def delete(current_user, self):
        if current_user.role_id < 2:
            return jsonify({'message' : 'Access denied'}) 
        id = request.args.get('id')
        query = PersonalTasks.query.filter_by(id=id)
        if query.first():
            query.delete()
            dataBase.session.commit()
            return jsonify({'message' : 'Task deleted'})     
        else:
            return jsonify({'message' : 'Task not found'})                 

class TeamTasksCRUD(Resource):
    @token_required
    def post(current_user, self):
        if current_user.role_id < 2:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json')
        data = request.get_json()
        date = datetime.strptime(data['task_date'], '%Y-%m-%d %H:%M:%S')

        new_task = TeamTasks(id=None, task_date=date, team_id=data['team_id'], description=data['description'], done=False)
        dataBase.session.add(new_task)
        dataBase.session.commit()
        return jsonify({'message' : 'Task succesfully added'})  

    @token_required
    def get(current_user, self):
        task_id = request.args.get('task_id')
        task_date = request.args.get('task_date')
        team_id = request.args.get('team_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        coach_id = request.args.get('coach_id')

        if task_id is not None:
            personal_tasks = TeamTasks.query.filter(TeamTasks.id == task_id).all()
            return personal_tasks.json()

        if start_date is not None and end_date is not None and team_id is not None:
            start = datetime.strptime(start_date, '%Y-%m-%d-%H:%M:%S')
            end = datetime.strptime(end_date, '%Y-%m-%d-%H:%M:%S')
            personal_tasks = TeamTasks.query.filter(TeamTasks.task_date >= start, TeamTasks.task_date <= end, TeamTasks.team_id == team_id).all()
            return serialize_list(personal_tasks)

        if coach_id is not None:
            personal_tasks = TeamTasks.query.join(TeamTasks.team).filter(Teams.coach_id == coach_id).all()
            return serialize_list(personal_tasks)

        if task_date is not None and team_id is not None:
            date = datetime.strptime(task_date, '%Y-%m-%d-%H:%M:%S')
            personal_tasks = TeamTasks.query.filter(TeamTasks.task_date == date, TeamTasks.team_id == team_id).all()
            return serialize_list(personal_tasks)

        if task_date is not None:
            date = datetime.strptime(task_date, '%Y-%m-%d-%H:%M:%S')
            personal_tasks = TeamTasks.query.filter(TeamTasks.task_date == date).all()
            return serialize_list(personal_tasks)

        if team_id is not None:
            personal_tasks = TeamTasks.query.filter(TeamTasks.team_id == team_id).all()
            return serialize_list(personal_tasks)

    @token_required
    def patch(current_user, self):

        data = request.json

        task = TeamTasks.query.filter_by(id=data['id']).first()
        if current_user.role.id >=  2:
            task.task_date = datetime.strptime(data['task_date'], '%Y-%m-%d')
            task.team_id = data['team_id']
            task.description = data['description']
        task.done = data['done']

        dataBase.session.commit()

        return jsonify({'message' : 'Task succesfully updated'})  

    @token_required
    def delete(current_user, self):
        if current_user.role < 2:
            return jsonify({'message' : 'Access denied'}) 
        id = request.args.get('id')
        query = TeamTasks.query.filter_by(id=id)
        if query.first():
            query.delete()
            dataBase.session.commit()
            return jsonify({'message' : 'Task deleted'})     
        else:
            return jsonify({'message' : 'Task not found'})

class MessageCRUD(Resource):

    @token_required
    def post(current_user, self):

        data = request.get_json()
        sender_id = current_user.id

        reciever_id = data['reciever_id']
        message = data['message']
        if len(message) > 2049:
            return Response("{'message':'Message too long'}", status=500, mimetype='application/json')    
        time_stamp = datetime.now()

        new_message = Messages(id=None, reciever_id=reciever_id, sender_id=sender_id, message=message, time_stamp=time_stamp)
        dataBase.session.add(new_message)
        dataBase.session.commit()

        return jsonify({'message' : 'Message succesfully added'})  

    @token_required
    def get(current_user, self):

        reciever_id = request.args.get('reciever_id')
        sender_id = request.args.get('sender_id')
        user_id = request.args.get('user_id')

        if user_id is not None:

            messages_recv = dataBase.session.query(Messages.sender_id, func.max(Messages.time_stamp)).filter(Messages.reciever_id == user_id).group_by(Messages.sender_id).order_by(func.max(Messages.time_stamp).desc()).all()

            messes = []
            for m in messages_recv:
                mess = {}

                message = dataBase.session.query(Users.first_name, Users.last_name, Messages.message, Messages.sender_id, Messages.time_stamp).filter(Messages.sender_id == m[0], Messages.time_stamp == m[1], Users.id == m[0]).group_by(Messages.sender_id).order_by(Messages.time_stamp.desc()).first()

                mess['first_name'] = message[0]
                mess['last_name'] = message[1]
                mess['message'] = message[2]
                mess['from_id'] = message[3]
                mess['date'] = str(message[4])
                messes.append(mess)

            return jsonify(messes)

        if current_user.id == reciever_id or current_user.id == sender_id:
            if sender_id is not None and reciever_id is not None:
                messages = dataBase.session.query(Users.first_name, Users.last_name, Messages.message, Messages.sender_id, Messages.reciever_id, Messages.time_stamp).filter(Messages.reciever_id.in_([reciever_id, sender_id]), Messages.sender_id.in_([reciever_id, sender_id]), Users.id == Messages.sender_id).order_by(Messages.time_stamp).all()
                
                messes = []

                for message in messages:
                    mess = {}
                    mess['first_name'] = message[0]
                    mess['last_name'] = message[1]
                    mess['message'] = message[2]
                    mess['sender_id'] = message[3]
                    mess['reciever_id'] = message[4]
                    mess['date'] = str(message[5])
                    messes.append(mess)
            
            return jsonify(messes)

        else:
            return jsonify({'message' : 'Don\'t be retard'})  
        
class TeamMessageCRUD(Resource):
    @token_required
    def post(current_user, self):

        data = request.get_json()

        sender_id = current_user.id
        team_id = data['team_id']
        message = data['message']

        valid = False
        if current_user.role_id != 2:
            for t in current_user.player[0].teams:
                if t.team.id == int(team_id):
                    valid = True
        else:
            valid = True
        
        if valid:
            if len(message) > 2049:
                return Response("{'message':'Message too long'}", status=500, mimetype='application/json')  
            time_stamp = datetime.now()

            new_message = TeamMessages(id=None, team_id=team_id, sender_id=sender_id, message=message, time_stamp=time_stamp)
            dataBase.session.add(new_message)
            dataBase.session.commit()
            return jsonify({'message' : 'Message succesfully added'})  
        else:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json')  

    @token_required
    def get(current_user, self):

        team_id = request.args.get('team_id')

        valid = False
        if current_user.role_id != 2:
            for t in current_user.player[0].teams:
                if t.team.id == int(team_id):
                    valid = True
        else:
            valid = True

        if valid:
            if team_id is not None:
                messages = dataBase.session.query(Users.first_name, Users.last_name, TeamMessages.message, TeamMessages.sender_id, TeamMessages.time_stamp).filter(TeamMessages.team_id == team_id, Users.id == TeamMessages.sender_id).order_by(TeamMessages.time_stamp).all()

                messes = []

                for message in messages:
                    mess = {}
                    mess['first_name'] = message[0]
                    mess['last_name'] = message[1]
                    mess['message'] = message[2]
                    mess['sender_id'] = message[3]
                    mess['date'] = str(message[4])
                    messes.append(mess)

            return jsonify(messes)
        else:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json')   

class TeamAssignment(Resource):
    @token_required
    def post(current_user, self):
        if current_user.role_id < 2:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json')
        data = request.get_json()
        team_id = data['team_id']
        player_id = data['player_id']
        query = TeamsPlayersAssociations.query.filter_by(player_id=player_id, team_id=team_id)
        if not query.first():
            new_assigment = TeamsPlayersAssociations(team_id=team_id, player_id=player_id, role=None)
            dataBase.session.add(new_assigment)
            dataBase.session.commit()
            return jsonify({'message' : 'Assigment added'})  
        else:
            return Response("{'message':'Assigment already exists'}", status=500, mimetype='application/json')  
                        
    @token_required
    def delete(current_user, self):
        if current_user.role_id < 2:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json')
        player_id = request.args.get('player_id')
        team_id = request.args.get('team_id')

        query = TeamsPlayersAssociations.query.filter_by(player_id=player_id, team_id=team_id)

        if query.first():
            query.delete()
            dataBase.session.commit()
            return jsonify({'message' : 'Assigment deleted'})  
        else:
            return Response("{'message':'Assigment not found'}", status=500, mimetype='application/json')

class Login(Resource):
    def post(self):
        
        auth = request.get_json()
        if not auth or not auth['email'] or not auth['password']:
            return make_response('Could not verify1', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

        user = Users.query.filter_by(email=auth['email']).first()

        if not user:
            return make_response('Could not verify2', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

        print(user.password_hash)
        if check_password_hash(user.password_hash, auth['password']):
            token = jwt.encode({'id' : user.id, 'exp' : datetime.utcnow() + timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm="HS512")

            response = make_response({'Message' : 'Login successfull'})
            response.set_cookie('token', token, httponly = True, secure=True, samesite="None")
            return response
        
        return make_response('Could not verify3', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

class Register(Resource):
    def post(self):
        data = request.get_json()

        #chceck if email already exists
        users_email = Users.query.filter_by(email=data['email']).first()
        if users_email:
            return jsonify({'message' : 'User with provided email address already exist!'})

        hashed_password = generate_password_hash(data['password'], method='sha256')

        id = str(uuid.uuid4())

        new_user = Users(id=id, first_name=data['first_name'], last_name=data['last_name'], email=data['email'], password_hash=hashed_password, role_id=1)
        
        new_player = Players(id=None, user_id=id)

        dataBase.session.add(new_user)
        dataBase.session.add(new_player)
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

class Get_Coaches_uid(Resource):
    @token_required
    def get(current_user, self):
        if current_user.role_id >= 2:
            users = Users.query.join(Users.coach).all()
            return serialize_list(users)
        else:
            return Response("{'message':'Permission denied'}", status=403, mimetype='application/json')    


api.add_resource(UsersCRUD, '/user')
api.add_resource(CoachCRUD, '/coach')
api.add_resource(PlayerCRUD, '/player')
api.add_resource(TeamCRUD, '/team')
api.add_resource(PersonalTasksCRUD, '/personal_task')
api.add_resource(TeamTasksCRUD, '/team_task')
api.add_resource(MessageCRUD, '/message')
api.add_resource(TeamMessageCRUD, '/team_message')
api.add_resource(Get_Coaches_uid, '/secret')


api.add_resource(Login, '/login')
api.add_resource(Register, '/register')
api.add_resource(Logout, '/logout')
api.add_resource(Account, '/account')
api.add_resource(TeamAssignment, '/team_assignment')



def main(*args, **kwargs):
    dataBase.create_all()
    #port = int(os.environ.get('PORT', 5000))
    #app.run(debug=True, host='0.0.0.0')
    

if __name__ == '__main__':
    main()
else:
    gmain = main()
