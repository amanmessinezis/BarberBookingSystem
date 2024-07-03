import os
import pytest
from app import app, db, User, Barber, Barbershop, Service
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()
        yield client
        db.drop_all()


@pytest.fixture
def setup_database():
    with app.app_context():
        # Create a barber with a hashed password
        hashed_password = generate_password_hash("password", method='pbkdf2:sha256')
        barber = Barber(first_name="Barber", last_name="User", email="barber@example.com", password=hashed_password)
        db.session.add(barber)
        db.session.commit()

        # Create a barbershop and assign the barber to it
        barbershop = Barbershop(name="Test Barbershop", address="123 Barber St", phone_number="1234567890",
                                creator_id=barber.id)
        db.session.add(barbershop)
        db.session.commit()

        barber.shop_id = barbershop.shop_id
        db.session.commit()

        yield db


def test_add_service(client, setup_database):
    # Sign in as the barber
    client.post('/signin', data=dict(email="barber@example.com", password="password"), follow_redirects=True)

    # Navigate to add service page
    response = client.get('/add_service', follow_redirects=True)
    assert response.status_code == 200
    assert b"Add Service" in response.data

    # Add a new service
    response = client.post('/save_service', data=dict(
        name="Beard Trim",
        duration=20,
        price=15.0
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Service added successfully" in response.data

    # Verify the service is added
    response = client.get('/barber_home', follow_redirects=True)
    assert response.status_code == 200
    assert b"Beard Trim" in response.data
