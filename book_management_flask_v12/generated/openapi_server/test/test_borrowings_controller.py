import unittest

from flask import json

from openapi_server.models.borrowings_get200_response import BorrowingsGet200Response  # noqa: E501
from openapi_server.models.borrowings_post_request import BorrowingsPostRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestBorrowingsController(BaseTestCase):
    """BorrowingsController integration test stubs"""

    def test_borrowings_get(self):
        """Test case for borrowings_get

        List all borrowings (paginated)
        """
        query_string = [('page', 56),
                        ('size', 56)]
        headers = { 
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/borrowings',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_borrowings_id_return_post(self):
        """Test case for borrowings_id_return_post

        Return a borrowed book
        """
        headers = { 
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/borrowings/{id}/return'.format(id=56),
            method='POST',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_borrowings_post(self):
        """Test case for borrowings_post

        Borrow a book copy
        """
        borrowings_post_request = openapi_server.BorrowingsPostRequest()
        headers = { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/borrowings',
            method='POST',
            headers=headers,
            data=json.dumps(borrowings_post_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
