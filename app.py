from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
import os

GET = 'GET'
POST = 'POST'


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "planets.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

db = SQLAlchemy(app)
ma = Marshmallow(app)


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
@app.route('/planets', methods=[GET])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)

    return jsonify(result)


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
