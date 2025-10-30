import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.borrowings_get200_response import BorrowingsGet200Response  # noqa: E501
from openapi_server.models.borrowings_post_request import BorrowingsPostRequest  # noqa: E501
from openapi_server import util


def borrowings_get(page=None, size=None):  # noqa: E501
    """List all borrowings (paginated)

     # noqa: E501

    :param page: 
    :type page: int
    :param size: 
    :type size: int

    :rtype: Union[BorrowingsGet200Response, Tuple[BorrowingsGet200Response, int], Tuple[BorrowingsGet200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def borrowings_id_return_post(id):  # noqa: E501
    """Return a borrowed book

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def borrowings_post(body):  # noqa: E501
    """Borrow a book copy

     # noqa: E501

    :param borrowings_post_request: 
    :type borrowings_post_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    borrowings_post_request = body
    if connexion.request.is_json:
        borrowings_post_request = BorrowingsPostRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
