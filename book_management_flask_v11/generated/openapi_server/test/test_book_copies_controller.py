import unittest

from flask import json

from openapi_server.models.book_copies_get200_response import BookCopiesGet200Response  # noqa: E501
from openapi_server.models.book_copies_id_put_request import BookCopiesIdPutRequest  # noqa: E501
from openapi_server.models.book_copies_post_request import BookCopiesPostRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestBookCopiesController(BaseTestCase):
    """BookCopiesController integration test stubs"""

    def test_book_copies_get(self):
        """Test case for book_copies_get

        Get all book copies (paginated, cached)
        """
        query_string = [('page', 56),
                        ('size', 56)]
        headers = { 
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/book_copies',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_book_copies_id_delete(self):
        """Test case for book_copies_id_delete

        Delete a book copy
        """
        headers = { 
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/book_copies/{id}'.format(id=56),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_book_copies_id_put(self):
        """Test case for book_copies_id_put

        Update a book copy
        """
        book_copies_id_put_request = openapi_server.BookCopiesIdPutRequest()
        headers = { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/book_copies/{id}'.format(id=56),
            method='PUT',
            headers=headers,
            data=json.dumps(book_copies_id_put_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_book_copies_post(self):
        """Test case for book_copies_post

        Create new book copy
        """
        book_copies_post_request = openapi_server.BookCopiesPostRequest()
        headers = { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/book_copies',
            method='POST',
            headers=headers,
            data=json.dumps(book_copies_post_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
