import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.book_title_detail import BookTitleDetail  # noqa: E501
from openapi_server.models.book_titles_get200_response import BookTitlesGet200Response  # noqa: E501
from openapi_server.models.book_titles_id_put_request import BookTitlesIdPutRequest  # noqa: E501
from openapi_server.models.book_titles_post_request import BookTitlesPostRequest  # noqa: E501
from openapi_server import util


def book_titles_get(page=None, size=None):  # noqa: E501
    """Get all book titles (paginated, cached)

     # noqa: E501

    :param page: 
    :type page: int
    :param size: 
    :type size: int

    :rtype: Union[BookTitlesGet200Response, Tuple[BookTitlesGet200Response, int], Tuple[BookTitlesGet200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def book_titles_id_delete(id):  # noqa: E501
    """Delete a book title

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def book_titles_id_get(id):  # noqa: E501
    """Get book title by ID

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[BookTitleDetail, Tuple[BookTitleDetail, int], Tuple[BookTitleDetail, int, Dict[str, str]]
    """
    return 'do some magic!'


def book_titles_id_put(id, body=None):  # noqa: E501
    """Update a book title

     # noqa: E501

    :param id: 
    :type id: int
    :param book_titles_id_put_request: 
    :type book_titles_id_put_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    book_titles_id_put_request = body
    if connexion.request.is_json:
        book_titles_id_put_request = BookTitlesIdPutRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def book_titles_post(body):  # noqa: E501
    """Create new book title

     # noqa: E501

    :param book_titles_post_request: 
    :type book_titles_post_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    book_titles_post_request = body
    if connexion.request.is_json:
        book_titles_post_request = BookTitlesPostRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
