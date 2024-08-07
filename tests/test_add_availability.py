from datetime import datetime
import pytest
from werkzeug.security import generate_password_hash
from app import app, db, Barber, Barbershop


# Fixture to configure the test client and in-memory database
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()
        yield client
        db.drop_all()


# Fixture to set up initial database state with a barber and barbershop
@pytest.fixture
def setup_database():
    with app.app_context():
        hashed_password = generate_password_hash("password", method='pbkdf2:sha256')
        barber = Barber(first_name="Barber", last_name="User", email="barber@example.com", password=hashed_password)
        db.session.add(barber)
        db.session.commit()

        barbershop = Barbershop(name="Test Barbershop", address="123 Barber St", phone_number="1234567890",
                                creator_id=barber.id)
        db.session.add(barbershop)
        db.session.commit()

        barber.shop_id = barbershop.shop_id
        db.session.commit()

        yield db


# Test case to add availability for a barber
def test_add_availability(client, setup_database):
    # Sign in as the barber
    client.post('/signin', data=dict(email="barber@example.com", password="password"), follow_redirects=True)

    # Navigate to add availability page
    response = client.get('/add_availability', follow_redirects=True)
    assert response.status_code == 200
    assert b"Add Availability" in response.data

    # Add a new availability
    response = client.post('/save_availability', data=dict(
        date=datetime.today().date().isoformat(),
        start_time="09:00",
        end_time="17:00"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Availability added successfully" in response.data

    # Verify the availability is added
    response = client.get('/barber_home', follow_redirects=True)
    assert response.status_code == 200
    assert datetime.today().date().isoformat().encode() in response.data
    assert b"09:00" in response.data
    assert b"17:00" in response.data
