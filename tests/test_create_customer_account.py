import pytest
from app import Customer
from app import app, db


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


# Test case to create a customer account
def test_create_customer_account(client):
    response = client.post('/', data=dict(
        first_name="Customer",
        last_name="User",
        email="customer@example.com",
        password="password",
        confirm_password="password",
        user_type="customer"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Account created successfully" in response.data

    # Verify the customer account is created in the database
    customer = Customer.query.filter_by(email="customer@example.com").first()
    assert customer is not None


# Test case to sign in to a customer account
def test_signin_customer_account(client):
    # First, create a customer account
    client.post('/', data=dict(
        first_name="Customer",
        last_name="User",
        email="customer@example.com",
        password="password",
        confirm_password="password",
        user_type="customer"
    ), follow_redirects=True)

    # Now, sign in to the customer account
    response = client.post('/signin', data=dict(
        email="customer@example.com",
        password="password"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome" in response.data
