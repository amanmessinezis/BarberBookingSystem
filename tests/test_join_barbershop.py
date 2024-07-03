import pytest
from werkzeug.security import generate_password_hash

from app import app, db, Barber, Barbershop


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
        barber1 = Barber(first_name="Barber1", last_name="User", email="barber1@example.com", password=hashed_password)
        db.session.add(barber1)
        db.session.commit()

        barber2 = Barber(first_name="Barber2", last_name="User", email="barber2@example.com", password=hashed_password)
        db.session.add(barber2)
        db.session.commit()

        # Create an existing barbershop
        barbershop = Barbershop(name="Existing Barbershop", address="789 Barber Lane", phone_number="1234509876",
                                creator_id=barber1.id)
        db.session.add(barbershop)
        db.session.commit()

        yield db


def test_join_barbershop(client, setup_database):
    # Sign in as the second barber
    client.post('/signin', data=dict(email="barber2@example.com", password="password"), follow_redirects=True)

    # Search for the existing barbershop
    response = client.get('/search_barbershop?search=Existing', follow_redirects=True)
    assert response.status_code == 200
    assert b"Existing Barbershop" in response.data

    # Join the existing barbershop
    barbershop = Barbershop.query.filter_by(name="Existing Barbershop").first()
    response = client.post(f'/join_barbershop/{barbershop.shop_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b"Joined barbershop successfully" in response.data

    # Verify the barber is now associated with the barbershop
    response = client.get('/barber_home', follow_redirects=True)
    assert response.status_code == 200
    assert b"Existing Barbershop" in response.data
    assert b"789 Barber Lane" in response.data
    assert b"1234509876" in response.data
