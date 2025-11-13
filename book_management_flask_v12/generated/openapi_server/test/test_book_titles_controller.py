import unittest

from flask import json

from openapi_server.models.book_title_detail import BookTitleDetail  # noqa: E501
from openapi_server.models.book_titles_get200_response import BookTitlesGet200Response  # noqa: E501
from openapi_server.models.book_titles_id_put_request import BookTitlesIdPutRequest  # noqa: E501
from openapi_server.models.book_titles_post_request import BookTitlesPostRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestBookTitlesController(BaseTestCase):
    """BookTitlesController integration test stubs"""

    def test_book_titles_get(self):
        """Test case for book_titles_get

        Get all book titles (paginated, cached)
        """
        query_string = [('page', 56),
                        ('size', 56)]
        headers = { 
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/book_titles',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_book_titles_id_delete(self):
        """Test case for book_titles_id_delete

        Delete a book title
        """
        headers = { 
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/book_titles/{id}'.format(id=56),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_book_titles_id_get(self):
        """Test case for book_titles_id_get

        Get book title by ID
        """
        headers = { 
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/book_titles/{id}'.format(id=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_book_titles_id_put(self):
        """Test case for book_titles_id_put

        Update a book title
        """
        book_titles_id_put_request = openapi_server.BookTitlesIdPutRequest()
        headers = { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/book_titles/{id}'.format(id=56),
            method='PUT',
            headers=headers,
            data=json.dumps(book_titles_id_put_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_book_titles_post(self):
        """Test case for book_titles_post

        Create new book title
        """
        book_titles_post_request = openapi_server.BookTitlesPostRequest()
        headers = { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/api/book_titles',
            method='POST',
            headers=headers,
            data=json.dumps(book_titles_post_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
