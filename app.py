from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
import os

GET = 'GET'
POST = 'POST'
PUT = 'PUT'


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "planets.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)

# cli commands
@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped!')


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star='Sol',
                     mass=3.258e23,
                     radius=1516,
                     distance=35.98e6
                     )

    venus = Planet(planet_name='Venus',
                   planet_type='Class E',
                   home_star='Sol',
                   mass=3.258e23,
                   radius=2516,
                   distance=35.98e6
                   )

    earth = Planet(planet_name='Earth',
                   planet_type='Class A',
                   home_star='Sol',
                   mass=4.258e23,
                   radius=3516,
                   distance=45.98e6
                   )

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='Aarav',
                     last_name='K',
                     email='aarav@yopmail.com',
                     password='password')

    db.session.add(test_user)
    db.session.commit()

    print('Database seeded!')


# endpoints
@app.route('/register', methods=[POST])
def register():
    email = request.json['email']

    user_exists_already = User.query.filter_by(email=email).first()
    if user_exists_already:
        return jsonify(message="Email already exists!"), 409

    first_name = request.json['first_name']
    last_name = request.json['last_name']
    password = request.json['password']

    user = User(first_name=first_name, last_name=last_name, email=email, password=password)
    db.session.add(user)
    db.session.commit()

    return jsonify(message="User created successfully!"),


@app.route('/login', methods=[POST])
def login():
    email = request.json['email']
    password = request.json['password']

    user_exists_already = User.query.filter_by(email=email, password=password).first()
    if not user_exists_already:
        return jsonify(message="Invalid credentials!"), 401

    access_token = create_access_token(identity=email)
    return jsonify(message="Login succeeded!", access_token=access_token)


@app.route('/reset_password/<string:email>', methods=[GET])
def reset_password(email: str):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify(message="Email doesn't exist!"), 401

    message = Message(subject="Planetary account reset password request",
                      body=f"Your planetary account password is {user.password}",
                      sender="admin@yeshu.in",
                      recipients=[email])
    mail.send(message)

    return jsonify(message=f"Password sent to {email}")


@app.route('/planets', methods=[GET])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)

    return jsonify(result)


@app.route('/planets', methods=[POST])
@jwt_required
def add_planet():
    planet_name = request.json['planet_name']

    planet_exists = Planet.query.filter_by(planet_name=planet_name).first()
    if planet_exists:
        return jsonify(message="Planet name already exist!"), 409

    planet_type = request.json['planet_type']
    home_star = request.json['home_star']
    mass = float(request.json['mass'])
    radius = float(request.json['radius'])
    distance = float(request.json['distance'])

    planet = Planet(planet_name=planet_name,
                    planet_type=planet_type,
                    home_star=home_star,
                    mass=mass,
                    radius=radius,
                    distance=distance)

    db.session.add(planet)
    db.session.commit()

    return jsonify(message="Planet created successfully!"), 201


@app.route('/planet/<int:planet_id>', methods=[GET])
def planet_details(planet_id):
    planet = Planet.query.filter_by(planet_id=planet_id).first()

    if not planet:
        return jsonify(message="That planet does not exist!"), 404

    result = planet_schema.dump(planet)

    return jsonify(result)


@app.route('/planet/<int:planet_id>', methods=[PUT])
def update_planet(planet_id):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if not planet:
        return jsonify(message="Planet not found!"), 404

    # updating fields
    if request.json.get('planet_name'):
        planet_name = request.json['planet_name']
        planet_exists = Planet.query.filter_by(planet_name=planet_name).first()
        if planet_exists:
            return jsonify(message="Planet name already exist!"), 409

        planet.planet_name = request.json['planet_name']
    if request.json.get('planet_type'):
        planet.planet_type = request.json['planet_type']
    if request.json.get('home_star'):
        planet.home_star = request.json['home_star']
    if request.json.get('mass'):
        planet.mass = float(request.json['mass'])
    if request.json.get('radius'):
        planet.radius = float(request.json['radius'])
    if request.json.get('distance'):
        planet.distance = float(request.json['distance'])

    db.session.commit()

    return jsonify(message="Planet updated successfully!"), 202


# database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


# database schemas
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)

if __name__ == '__main__':
    app.run()
