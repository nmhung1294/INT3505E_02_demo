"""
Test OAuth2 Introspection for Book Management Flask v7

This test suite covers:
1. JWT authentication mode (default)
2. OAuth2 introspection mode
3. Token validation scenarios
4. Error handling
"""

import pytest
import jwt
import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

# Add parent directory to path to allow importing book_management_flask_v7
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from book_management_flask_v7 import app as flask_app, db
from book_management_flask_v7.models import User, BookTitle, BookCopy
import book_management_flask_v7.api as api_module

# Get the SECRET_KEY from the api module
SECRET_KEY = api_module.SECRET_KEY


@pytest.fixture
def app():
    """Configure application for testing"""
    # Store original config values
    original_config = {}
    config_keys = ['TESTING', 'SQLALCHEMY_DATABASE_URI', 'AUTH_MODE']
    for key in config_keys:
        if key in flask_app.config:
            original_config[key] = flask_app.config[key]
    
    # Set test configuration
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['AUTH_MODE'] = 'jwt'  # Default to JWT mode
    
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        # Create test user
        user = User(id=1, name='Test User', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        
    yield flask_app
    
    # Cleanup
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
    
    # Restore original config
    for key, value in original_config.items():
        flask_app.config[key] = value


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    """Generate valid JWT token for testing"""
    with app.app_context():
        token = jwt.encode(
            {'id': 1, 'exp': datetime.utcnow() + timedelta(hours=1)},
            SECRET_KEY,
            algorithm='HS256'
        )
    return {'Authorization': f'Bearer {token}'}


def get_error_message(response):
    """Helper to extract error message from HTML or JSON response"""
    try:
        return json.loads(response.data)['message']
    except:
        # Parse HTML response
        text = response.data.decode('utf-8')
        if '<p>' in text and '</p>' in text:
            start = text.find('<p>') + 3
            end = text.find('</p>', start)
            return text[start:end]
        return text


class TestJWTAuthentication:
    """Test JWT authentication mode (default)"""
    
    def test_access_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get('/api/book_titles')
        assert response.status_code == 401
        assert 'Missing token' in get_error_message(response)
    
    def test_access_with_invalid_token(self, client):
        """Test accessing with invalid JWT token"""
        headers = {'Authorization': 'Bearer invalid_token_here'}
        response = client.get('/api/book_titles', headers=headers)
        assert response.status_code == 401
        assert 'Invalid token' in get_error_message(response)
    
    def test_access_with_expired_token(self, app, client):
        """Test accessing with expired JWT token"""
        with app.app_context():
            expired_token = jwt.encode(
                {'id': 1, 'exp': datetime.utcnow() - timedelta(hours=1)},
                SECRET_KEY,
                algorithm='HS256'
            )
        headers = {'Authorization': f'Bearer {expired_token}'}
        response = client.get('/api/book_titles', headers=headers)
        assert response.status_code == 401
    
    def test_access_with_valid_token(self, client, auth_headers):
        """Test accessing with valid JWT token"""
        response = client.get('/api/book_titles', headers=auth_headers)
        assert response.status_code == 200
    
    def test_access_with_nonexistent_user(self, app, client):
        """Test JWT token with non-existent user ID"""
        with app.app_context():
            token = jwt.encode(
                {'id': 999, 'exp': datetime.utcnow() + timedelta(hours=1)},
                SECRET_KEY,
                algorithm='HS256'
            )
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/api/book_titles', headers=headers)
        assert response.status_code == 401
        assert 'Invalid user' in get_error_message(response)
    
    def test_malformed_authorization_header(self, client):
        """Test malformed Authorization header"""
        # Missing Bearer prefix
        headers = {'Authorization': 'not_bearer_token'}
        response = client.get('/api/book_titles', headers=headers)
        assert response.status_code == 401
        
        # Empty token
        headers = {'Authorization': 'Bearer '}
        response = client.get('/api/book_titles', headers=headers)
        assert response.status_code == 401


class TestOAuth2Introspection:
    """Test OAuth2 introspection mode"""
    
    def test_oauth2_mode_success(self, app, client):
        """Test successful OAuth2 introspection"""
        app.config['AUTH_MODE'] = 'oauth2'
        app.config['OAUTH2_INTROSPECTION_URL'] = 'https://oauth.example.com/introspect'
        app.config['OAUTH2_INTROSPECTION_CLIENT_ID'] = 'client_id'
        app.config['OAUTH2_INTROSPECTION_CLIENT_SECRET'] = 'client_secret'
        app.config['OAUTH2_USER_ID_FIELD'] = 'sub'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'active': True,
            'sub': '1',
            'scope': 'read write',
            'client_id': 'client_id',
            'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }
        
        with patch('book_management_flask_v7.api.requests.post', return_value=mock_response) as mock_post:
            headers = {'Authorization': 'Bearer oauth2_token_here'}
            response = client.get('/api/book_titles', headers=headers)
            
            assert response.status_code == 200
            # Verify introspection was called with correct parameters
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == 'https://oauth.example.com/introspect'
            assert call_args[1]['data'] == {'token': 'oauth2_token_here'}
            assert call_args[1]['auth'] == ('client_id', 'client_secret')
    
    def test_oauth2_inactive_token(self, app, client):
        """Test OAuth2 introspection with inactive token"""
        app.config['AUTH_MODE'] = 'oauth2'
        app.config['OAUTH2_INTROSPECTION_URL'] = 'https://oauth.example.com/introspect'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'active': False}
        
        with patch('book_management_flask_v7.api.requests.post', return_value=mock_response):
            headers = {'Authorization': 'Bearer inactive_token'}
            response = client.get('/api/book_titles', headers=headers)
            
            assert response.status_code == 401
            assert 'Token inactive' in get_error_message(response)
    
    def test_oauth2_missing_user_id(self, app, client):
        """Test OAuth2 introspection response missing user ID"""
        app.config['AUTH_MODE'] = 'oauth2'
        app.config['OAUTH2_INTROSPECTION_URL'] = 'https://oauth.example.com/introspect'
        app.config['OAUTH2_USER_ID_FIELD'] = 'sub'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'active': True,
            'scope': 'read write',
            # Missing 'sub' field
        }
        
        with patch('book_management_flask_v7.api.requests.post', return_value=mock_response):
            headers = {'Authorization': 'Bearer token_without_user_id'}
            response = client.get('/api/book_titles', headers=headers)
            
            assert response.status_code == 401
            assert 'User id not present' in get_error_message(response)
    
    def test_oauth2_introspection_endpoint_error(self, app, client):
        """Test OAuth2 introspection endpoint returning error"""
        app.config['AUTH_MODE'] = 'oauth2'
        app.config['OAUTH2_INTROSPECTION_URL'] = 'https://oauth.example.com/introspect'
        
        mock_response = Mock()
        mock_response.status_code = 401
        
        with patch('book_management_flask_v7.api.requests.post', return_value=mock_response):
            headers = {'Authorization': 'Bearer token'}
            response = client.get('/api/book_titles', headers=headers)
            
            assert response.status_code == 401
            assert 'Token introspection failed' in get_error_message(response)
    
    def test_oauth2_network_error(self, app, client):
        """Test OAuth2 introspection with network error"""
        app.config['AUTH_MODE'] = 'oauth2'
        app.config['OAUTH2_INTROSPECTION_URL'] = 'https://oauth.example.com/introspect'
        
        import requests
        with patch('book_management_flask_v7.api.requests.post', side_effect=requests.RequestException('Network error')):
            headers = {'Authorization': 'Bearer token'}
            response = client.get('/api/book_titles', headers=headers)
            
            assert response.status_code == 502
            assert 'Introspection request failed' in get_error_message(response)
    
    def test_oauth2_invalid_json_response(self, app, client):
        """Test OAuth2 introspection with invalid JSON response"""
        app.config['AUTH_MODE'] = 'oauth2'
        app.config['OAUTH2_INTROSPECTION_URL'] = 'https://oauth.example.com/introspect'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError('Invalid JSON')
        
        with patch('book_management_flask_v7.api.requests.post', return_value=mock_response):
            headers = {'Authorization': 'Bearer token'}
            response = client.get('/api/book_titles', headers=headers)
            
            assert response.status_code == 502
            assert 'Invalid JSON' in get_error_message(response)
    
    def test_oauth2_user_not_found(self, app, client):
        """Test OAuth2 introspection with non-existent user"""
        app.config['AUTH_MODE'] = 'oauth2'
        app.config['OAUTH2_INTROSPECTION_URL'] = 'https://oauth.example.com/introspect'
        app.config['OAUTH2_USER_ID_FIELD'] = 'sub'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'active': True,
            'sub': '999',  # Non-existent user
        }
        
        with patch('book_management_flask_v7.api.requests.post', return_value=mock_response):
            headers = {'Authorization': 'Bearer token'}
            response = client.get('/api/book_titles', headers=headers)
            
            assert response.status_code == 401
            assert 'User not found' in get_error_message(response)
    
    def test_oauth2_missing_introspection_url(self, app, client):
        """Test OAuth2 mode without configured introspection URL"""
        app.config['AUTH_MODE'] = 'oauth2'
        app.config['OAUTH2_INTROSPECTION_URL'] = None
        
        headers = {'Authorization': 'Bearer token'}
        response = client.get('/api/book_titles', headers=headers)
        
        assert response.status_code == 500
        assert 'OAuth2 introspection URL not configured' in get_error_message(response)
    
    def test_oauth2_without_client_credentials(self, app, client):
        """Test OAuth2 introspection without client credentials (should still work)"""
        app.config['AUTH_MODE'] = 'oauth2'
        app.config['OAUTH2_INTROSPECTION_URL'] = 'https://oauth.example.com/introspect'
        app.config['OAUTH2_INTROSPECTION_CLIENT_ID'] = None
        app.config['OAUTH2_INTROSPECTION_CLIENT_SECRET'] = None
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'active': True,
            'sub': '1',
        }
        
        with patch('book_management_flask_v7.api.requests.post', return_value=mock_response) as mock_post:
            headers = {'Authorization': 'Bearer token'}
            response = client.get('/api/book_titles', headers=headers)
            
            assert response.status_code == 200
            # Verify no HTTP Basic auth was used
            call_args = mock_post.call_args
            assert call_args[1]['auth'] is None
    
    def test_oauth2_custom_user_id_field(self, app, client):
        """Test OAuth2 introspection with custom user ID field"""
        app.config['AUTH_MODE'] = 'oauth2'
        app.config['OAUTH2_INTROSPECTION_URL'] = 'https://oauth.example.com/introspect'
        app.config['OAUTH2_USER_ID_FIELD'] = 'user_id'  # Custom field
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'active': True,
            'user_id': '1',  # Custom field name
            'scope': 'read write',
        }
        
        with patch('book_management_flask_v7.api.requests.post', return_value=mock_response):
            headers = {'Authorization': 'Bearer token'}
            response = client.get('/api/book_titles', headers=headers)
            
            assert response.status_code == 200


class TestAuthModeConfiguration:
    """Test authentication mode configuration"""
    
    def test_unknown_auth_mode(self, app, client):
        """Test with unknown AUTH_MODE"""
        app.config['AUTH_MODE'] = 'unknown_mode'
        
        headers = {'Authorization': 'Bearer token'}
        response = client.get('/api/book_titles', headers=headers)
        
        assert response.status_code == 500
        assert 'Unknown AUTH_MODE' in get_error_message(response)
    
    def test_default_auth_mode_is_jwt(self, app, client, auth_headers):
        """Test that default AUTH_MODE is JWT"""
        # Don't set AUTH_MODE explicitly
        if 'AUTH_MODE' in app.config:
            del app.config['AUTH_MODE']
        
        response = client.get('/api/book_titles', headers=auth_headers)
        assert response.status_code == 200


class TestPublicEndpoints:
    """Test that documentation endpoints are accessible without authentication"""
    
    def test_swagger_ui_access(self, client):
        """Test Swagger UI is accessible without token"""
        response = client.get('/swagger')
        # Should not return 401
        assert response.status_code != 401
    
    def test_openapi_yaml_access(self, client):
        """Test OpenAPI YAML is accessible without token"""
        response = client.get('/openapi.yaml')
        # Should not return 401
        assert response.status_code != 401


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios"""
    
    def test_full_jwt_workflow(self, client):
        """Test complete JWT authentication workflow"""
        # 1. Register user
        register_data = {
            'name': 'Integration Test User',
            'email': 'integration@test.com'
        }
        response = client.post('/api/auth/register', 
                              json=register_data,
                              headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        
        # 2. Login
        login_data = {'email': 'integration@test.com'}
        response = client.post('/api/auth/login',
                              json=login_data,
                              headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = json.loads(response.data)
        token = data['token']
        
        # 3. Access protected endpoint
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/api/book_titles', headers=headers)
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
