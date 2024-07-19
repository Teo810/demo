import pytest
from flask import url_for

from app import app, db, EventEntity, WeatherEntity
from datetime import datetime, date
from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Using in-memory SQLite for testing
    with app.app_context():
        db.create_all()
    test_client = app.test_client()
    yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def sample_event(client):
    with app.app_context():
        # Create the event within an app context, which should automatically manage the session
        event = EventEntity(city="TestCity", date=datetime.strptime("2020-01-01", "%Y-%m-%d"),
                            title="Test Event", description="A test event", active=True)
        db.session.add(event)
        db.session.commit()
        # Directly return the ID, assuming you may only need the ID and refetch it later
        return event.id


@pytest.fixture
def sample_weather(client):
    with app.app_context():
        weather = WeatherEntity(city="TestCity", date=datetime.strptime("2024-12-25", "%Y-%m-%d"),
                                temperature=25.5, humidity=70, description="Sunny", active=True)
        db.session.add(weather)
        db.session.commit()
        return weather.id


def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello World!' in response.data


def test_create_event(client):
    response = client.post('/events', json={
        'city': 'New City',
        'date': '2024-01-01',
        'title': 'New Year Event',
        'description': 'Celebration of the New Year.'
    })
    assert response.status_code == 201
    assert b'New Year Event' in response.data


def test_create_weather(client):
    response = client.post('/weather', json={
        'city': 'Sunny City',
        'date': '2024-06-15',
        'temperature': 30,
        'humidity': 60,
        'description': 'Very hot'
    })
    assert response.status_code == 201
    assert b'Very hot' in response.data


def test_get_event(client, sample_event):
    with app.app_context():
        fetched_event = EventEntity.query.get(sample_event)
        assert fetched_event is not None, "Event should exist in the database"
        response = client.get(f'/events/{fetched_event.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['title'] == 'Test Event'


def test_get_weather(client, sample_weather):
    with app.app_context():
        # Fetch the weather by ID to ensure it's properly retrieved from the active session.
        fetched_weather = WeatherEntity.query.get(sample_weather)
        assert fetched_weather is not None, "Weather should exist in the database"

        # Perform the GET request using the fetched ID.
        response = client.get(f'/weather/{fetched_weather.id}')
        assert response.status_code == 200

        # Verify that the JSON response contains the correct data.
        data = response.get_json()
        assert data['description'] == 'Sunny', "Weather description should match 'Sunny'"
