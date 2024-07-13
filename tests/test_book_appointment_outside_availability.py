from datetime import datetime, time
import pytest
from werkzeug.security import generate_password_hash
from app import app, db, Barber, Customer, Barbershop, Service, Availability


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


# Fixture to set up initial database state with a barber, barbershop, service, availability, and customer
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

        service = Service(barber_id=barber.id, name="Haircut", duration=30, price=25.0)
        db.session.add(service)
        db.session.commit()

        availability = Availability(barber_id=barber.id, date=datetime.today().date(), start_time=time(9, 0),
                                    end_time=time(17, 0))
        db.session.add(availability)
        db.session.commit()

        hashed_password = generate_password_hash("password", method='pbkdf2:sha256')
        customer = Customer(first_name="Customer", last_name="User", email="customer@example.com",
                            password=hashed_password)
        db.session.add(customer)
        db.session.commit()

        yield db


# Test case to book an appointment outside barber's availability
def test_book_appointment_outside_availability(client, setup_database):
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

    # Attempt to book an appointment outside of availability (e.g., at 18:00)
    service = Service.query.filter_by(name="Haircut").first()
    available_day = datetime.today().date().isoformat()
    response = client.post(f'/choose_time/{service.id}/{available_day}', data=dict(start_time="18:00"),
                           follow_redirects=True)
    assert response.status_code == 200
    assert b"flash-error" in response.data  # Ensure the error flash message is present
    assert b"Selected time is not within the barber&#39;s availability" in response.data  # Ensure the specific error message is present
