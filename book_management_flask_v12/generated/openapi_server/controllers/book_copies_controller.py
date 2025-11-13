import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.book_copies_get200_response import BookCopiesGet200Response  # noqa: E501
from openapi_server.models.book_copies_id_put_request import BookCopiesIdPutRequest  # noqa: E501
from openapi_server.models.book_copies_post_request import BookCopiesPostRequest  # noqa: E501
from openapi_server import util


def book_copies_get(page=None, size=None):  # noqa: E501
    """Get all book copies (paginated, cached)

     # noqa: E501

    :param page: 
    :type page: int
    :param size: 
    :type size: int

    :rtype: Union[BookCopiesGet200Response, Tuple[BookCopiesGet200Response, int], Tuple[BookCopiesGet200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def book_copies_id_delete(id):  # noqa: E501
    """Delete a book copy

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def book_copies_id_put(id, body=None):  # noqa: E501
    """Update a book copy

     # noqa: E501

    :param id: 
    :type id: int
    :param book_copies_id_put_request: 
    :type book_copies_id_put_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    book_copies_id_put_request = body
    if connexion.request.is_json:
        book_copies_id_put_request = BookCopiesIdPutRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def book_copies_post(body):  # noqa: E501
    """Create new book copy

     # noqa: E501

    :param book_copies_post_request: 
    :type book_copies_post_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    book_copies_post_request = body
    if connexion.request.is_json:
        book_copies_post_request = BookCopiesPostRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
