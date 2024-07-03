import pytest
from werkzeug.security import generate_password_hash

from app import Barber, Customer, Barbershop, Service
from app import app, db


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()
        yield client
        db.drop_all()


def test_barber_customer_flow(client):
    # Barber signs up
    barber_password = generate_password_hash("barberpassword", method='pbkdf2:sha256')
    barber = Barber(first_name="Barber", last_name="Test", email="barber@test.com", password=barber_password)
    db.session.add(barber)
    db.session.commit()

    # Barber logs in
    client.post('/signin', data=dict(email="barber@test.com", password="barberpassword"), follow_redirects=True)

    # Barber creates a barbershop
    response = client.post('/new_barbershop', data=dict(
        name="Test Barbershop",
        address="123 Barber St",
        phone_number="123-456-7890"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Barbershop created successfully." in response.data

    # Barber adds availability
    response = client.post('/save_availability', data=dict(
        date="2024-07-01",
        start_time="09:00",
        end_time="17:00"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Availability added successfully." in response.data

    # Barber adds a service
    response = client.post('/save_service', data=dict(
        name="Haircut",
        duration=30,
        price=20.0
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Service added successfully." in response.data

    # Customer signs up
    customer_password = generate_password_hash("customerpassword", method='pbkdf2:sha256')
    customer = Customer(first_name="Customer", last_name="Test", email="customer@test.com", password=customer_password)
    db.session.add(customer)
    db.session.commit()

    # Customer logs in
    client.post('/signin', data=dict(email="customer@test.com", password="customerpassword"), follow_redirects=True)

    # Customer searches for a barbershop
    response = client.get('/customer_search_barbershop?search=Test Barbershop', follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Barbershop" in response.data

    # Customer views barbers in the barbershop
    barbershop = Barbershop.query.filter_by(name="Test Barbershop").first()
    response = client.get(f'/view_barbers/{barbershop.shop_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b"Barber Test" in response.data

    # Customer books an appointment
    service = Service.query.filter_by(name="Haircut").first()
    response = client.get(f'/book_appointment/{service.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b"Book Appointment for Haircut" in response.data

    response = client.post(f'/choose_time/{service.id}/2024-07-01', data=dict(
        start_time="09:00"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Appointment confirmed." in response.data
