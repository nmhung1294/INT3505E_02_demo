import unittest

from flask import json

from openapi_server.models.auth_login_post200_response import AuthLoginPost200Response  # noqa: E501
from openapi_server.models.auth_login_post_request import AuthLoginPostRequest  # noqa: E501
from openapi_server.models.auth_register_post_request import AuthRegisterPostRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestAuthController(BaseTestCase):
    """AuthController integration test stubs"""

    def test_auth_login_post(self):
        """Test case for auth_login_post

        Login and get JWT token
        """
        auth_login_post_request = openapi_server.AuthLoginPostRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/auth/login',
            method='POST',
            headers=headers,
            data=json.dumps(auth_login_post_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_auth_register_post(self):
        """Test case for auth_register_post

        Register a new user
        """
        auth_register_post_request = openapi_server.AuthRegisterPostRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/auth/register',
            method='POST',
            headers=headers,
            data=json.dumps(auth_register_post_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
