import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auth_login_post200_response import AuthLoginPost200Response  # noqa: E501
from openapi_server.models.auth_login_post_request import AuthLoginPostRequest  # noqa: E501
from openapi_server.models.auth_register_post_request import AuthRegisterPostRequest  # noqa: E501
from openapi_server import util


def auth_login_post(body):  # noqa: E501
    """Login and get JWT token

     # noqa: E501

    :param auth_login_post_request: 
    :type auth_login_post_request: dict | bytes

    :rtype: Union[AuthLoginPost200Response, Tuple[AuthLoginPost200Response, int], Tuple[AuthLoginPost200Response, int, Dict[str, str]]
    """
    auth_login_post_request = body
    if connexion.request.is_json:
        auth_login_post_request = AuthLoginPostRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def auth_register_post(body):  # noqa: E501
    """Register a new user

     # noqa: E501

    :param auth_register_post_request: 
    :type auth_register_post_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    auth_register_post_request = body
    if connexion.request.is_json:
        auth_register_post_request = AuthRegisterPostRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
