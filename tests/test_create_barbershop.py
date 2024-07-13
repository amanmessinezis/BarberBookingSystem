import pytest
from werkzeug.security import generate_password_hash
from app import app, db, Barber


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


# Fixture to set up initial database state with a barber
@pytest.fixture
def setup_database():
    with app.app_context():
        hashed_password = generate_password_hash("password", method='pbkdf2:sha256')
        barber = Barber(first_name="Barber", last_name="User", email="barber@example.com", password=hashed_password)
        db.session.add(barber)
        db.session.commit()

        yield db


# Test case to create a barbershop
def test_create_barbershop(client, setup_database):
    # Sign in as the barber
    client.post('/signin', data=dict(email="barber@example.com", password="password"), follow_redirects=True)

    # Create a new barbershop
    response = client.post('/new_barbershop', data=dict(
        name="New Barbershop",
        address="456 Barber Blvd",
        phone_number="0987654321"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Barbershop created successfully" in response.data

    # Verify the barbershop is created
    response = client.get('/barber_home', follow_redirects=True)
    assert response.status_code == 200
    assert b"New Barbershop" in response.data
    assert b"456 Barber Blvd" in response.data
    assert b"0987654321" in response.data
