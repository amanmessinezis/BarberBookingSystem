import pytest
from app import app, db
from app import User
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


def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Create an Account" in response.data


def test_signin(client):
    hashed_password = generate_password_hash("testpassword", method='pbkdf2:sha256')
    user = User(first_name="Test", last_name="User", email="test@example.com", password=hashed_password,
                type="customer")
    db.session.add(user)
    db.session.commit()

    response = client.post('/signin', data=dict(email="test@example.com", password="testpassword"),
                           follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome" in response.data
