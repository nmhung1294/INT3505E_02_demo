import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.user import User  # noqa: E501
from openapi_server.models.users_get200_response import UsersGet200Response  # noqa: E501
from openapi_server import util


def users_get(page=None, size=None):  # noqa: E501
    """Get all users (paginated)

     # noqa: E501

    :param page: 
    :type page: int
    :param size: 
    :type size: int

    :rtype: Union[UsersGet200Response, Tuple[UsersGet200Response, int], Tuple[UsersGet200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def users_id_delete(id):  # noqa: E501
    """Delete a user

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def users_id_get(id):  # noqa: E501
    """Get user by ID

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]
    """
    return 'do some magic!'
