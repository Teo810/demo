from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from datetime import datetime, date
import os


app = Flask('CityBreakDB')


# Database configuration
db_host = os.environ.get('DB_HOST') or 'localhost'
db_user = os.environ.get('DB_USER') or 'myuser'
db_pw = os.environ.get('DB_PASSWORD') or 'mypassword'
db_name = 'citybreak'

db_url = f'mysql+mysqlconnector://{db_user}:{db_pw}@{db_host}/{db_name}'

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app)


@app.route('/')
def index():
    return '''<html><body><strong>Hello World!</strong><body></html>'''


class EventEntity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'date': self.date.strftime('%Y-%m-%d'),
            'title': self.title,
            'description': self.description,
            'active': self.active
        }


class WeatherEntity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'date': self.date.strftime('%Y-%m-%d'),
            'temperature': self.temperature,
            'humidity': self.humidity,
            'description': self.description,
            'active': self.active
        }


def validate_event(data):
    if not data.get('city') or not data.get('title'):
        abort(400, description="City and Title are required.")
    try:
        datetime.strptime(data['date'], '%Y-%m-%d')
    except ValueError:
        abort(400, description="Invalid date format. It should be YYYY-MM-DD.")


@app.route('/deactivate-past-events')
def deactivate_past_events():
    today = date.today()
    past_events = EventEntity.query.filter(EventEntity.date < today, EventEntity.active == True).all()
    print("Deactivating events:", [event.id for event in past_events])  # Debug: list events being deactivated
    for event in past_events:
        event.active = False
    db.session.commit()
    return jsonify({"message": "Past events deactivated", "count": len(past_events)}), 200



class EventsResource(Resource):
    def get(self, id=None):
        query = EventEntity.query.filter(EventEntity.active == True)
        if id:
            event = query.filter_by(id=id).first()  # Correctly apply the ID filter after the active filter
            if event:
                return event.to_dict()
            else:
                return {'message': 'Event not found'}, 404

        # Handling additional filtering based on URL parameters if 'id' is not provided
        args = request.args
        if 'name' in args:
            query = query.filter(EventEntity.title.like(f"%{args['name']}%"))
        if 'city' in args:
            query = query.filter_by(city=args['city'])
        elif 'date' in args:
            query = query.filter_by(date=args['date'])

        events = query.all()
        return [event.to_dict() for event in events]


    def post(self):
        data = request.get_json()
        validate_event(data)
        new_event = EventEntity(
            city=data['city'],
            date=data['date'],
            title=data['title'],
            description=data['description']
        )
        db.session.add(new_event)
        db.session.commit()
        return new_event.to_dict(), 201


    def put(self, id):
        event = EventEntity.query.get(id)
        if not event:
            return {'message': 'Event not found'}, 404
        data = request.get_json()
        event.city = data['city']
        event.date = data['date']
        event.title = data['title']
        event.description = data['description']
        db.session.commit()
        return event.to_dict()


    def delete(self, id):
        event = EventEntity.query.get(id)
        if not event:
            return {'message': 'Event not found'}, 404
        event.active = False
        db.session.commit()
        return '', 204


api.add_resource(EventsResource, '/events', '/events/<int:id>')


def validate_weather(data):
    if not data.get('city') or not data.get('date'):
        abort(400, description="City and Date are required.")
    try:
        datetime.strptime(data['date'], '%Y-%m-%d')
    except ValueError:
        abort(400, description="Invalid date format. It should be YYYY-MM-DD.")


@app.route('/deactivate-past-weather')
def deactivate_past_weather():
    past_weather = WeatherEntity.query.filter(WeatherEntity.date < date.today(), WeatherEntity.active == True).all()
    for weather in past_weather:
        weather.active = False
    db.session.commit()
    return 'Past weather records deactivated', 200


class WeatherResource(Resource):
    def get(self, id=None):
        query = WeatherEntity.query.filter(WeatherEntity.active == True)
        if id:
            # Instead of using .get(id), which fails with existing criteria, use .filter_by() and .first()
            weather = query.filter_by(id=id).first()
            if weather:
                return weather.to_dict()
            else:
                return {'message': 'Weather not found'}, 404

        args = request.args
        if 'city' in args:
            query = query.filter_by(city=args['city'])
        elif 'date' in args:
            query = query.filter_by(date=args['date'])

        weather_data = query.all()
        return [weather.to_dict() for weather in weather_data]


    def post(self):
        data = request.get_json()
        validate_weather(data)
        new_weather = WeatherEntity(
            city=data['city'],
            date=data['date'],
            temperature=data['temperature'],
            humidity=data['humidity'],
            description=data['description']
        )
        db.session.add(new_weather)
        db.session.commit()
        return new_weather.to_dict(), 201


    def put(self, id):
        weather = WeatherEntity.query.get(id)
        if not weather:
            return {'message': 'Weather not found'}, 404
        data = request.get_json()
        weather.city = data['city']
        weather.date = data['date']
        weather.temperature = data['temperature']
        weather.humidity = data['humidity']
        weather.description = data['description']
        db.session.commit()
        return weather.to_dict()


    def delete(self, id):
        weather = WeatherEntity.query.get(id)
        if not weather:
            return {'message': 'Weather not found'}, 404
        weather.active = False
        db.session.commit()
        return '', 204


api.add_resource(WeatherResource, '/weather', '/weather/<int:id>')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
