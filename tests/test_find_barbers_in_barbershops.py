import pytest
from werkzeug.security import generate_password_hash

from app import app, db, Barber, Customer, Barbershop, Service


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

        # Create a barbershop
        barbershop = Barbershop(name="Test Barbershop", address="123 Barber St", phone_number="1234567890",
                                creator_id=barber.id)
        db.session.add(barbershop)
        db.session.commit()

        # Assign barber to barbershop
        barber.shop_id = barbershop.shop_id
        db.session.commit()

        # Create a service provided by the barber
        service = Service(barber_id=barber.id, name="Haircut", duration=30, price=25.0)
        db.session.add(service)
        db.session.commit()

        # Create a customer with a hashed password
        hashed_password = generate_password_hash("password", method='pbkdf2:sha256')
        customer = Customer(first_name="Customer", last_name="User", email="customer@example.com",
                            password=hashed_password)
        db.session.add(customer)
        db.session.commit()

        yield db


def test_find_barbers_in_barbershops(client, setup_database):
    # Sign in as the customer
    client.post('/signin', data=dict(email="customer@example.com", password="password"), follow_redirects=True)

    # Perform search for barbershops
    response = client.get('/customer_search_barbershop?search=Test', follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Barbershop" in response.data

    # View barbers in the found barbershop
    barbershop = Barbershop.query.filter_by(name="Test Barbershop").first()
    response = client.get(f'/view_barbers/{barbershop.shop_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b"Barber User" in response.data
    assert b"Haircut" in response.data
    assert b"30 minutes" in response.data
    assert b"£25.0" in response.data
