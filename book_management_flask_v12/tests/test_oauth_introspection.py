import json
import pytest
from flask import url_for
from book_management_flask_v7 import app, db
from book_management_flask_v7.models import User


@pytest.fixture
def client(tmp_path, monkeypatch):
    app.config['TESTING'] = True
    app.config['AUTH_MODE'] = 'oauth2'
    # use a fake introspection URL (we'll monkeypatch requests.post)
    app.config['OAUTH2_INTROSPECTION_URL'] = 'https://introspect.local/token'
    # create DB in memory for tests
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            # ensure a clean database for each test run
            db.drop_all()
            db.create_all()
            # add a sample user with id 1
            u = User(name='Test', email='test@example.com')
            db.session.add(u)
            db.session.commit()
        yield client


class DummyResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json


def test_introspection_active_token(monkeypatch, client):
    # introspection returns active + sub = user id
    def fake_post(url, data, headers=None, auth=None, timeout=None):
        assert url == client.application.config['OAUTH2_INTROSPECTION_URL']
        assert data['token'] == 'valid-token'
        return DummyResponse(200, {'active': True, 'sub': 1})

    monkeypatch.setattr('requests.post', fake_post)

    rv = client.get('/api/book_titles', headers={'Authorization': 'Bearer valid-token'})
    assert rv.status_code == 200


def test_introspection_inactive_token(monkeypatch, client):
    def fake_post(url, data, headers=None, auth=None, timeout=None):
        return DummyResponse(200, {'active': False})

    monkeypatch.setattr('requests.post', fake_post)

    rv = client.get('/api/book_titles', headers={'Authorization': 'Bearer invalid-token'})
    assert rv.status_code == 401