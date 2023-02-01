import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from os import environ

import requests


@dataclass(frozen=True)
class Token:
    """ tumblr auth token """
    access_token: str
    expires_in: int
    id_token: bool
    scope: str
    token_type: str
    originally_issued: datetime = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "originally_issued", datetime.now())

    @property
    def expired(self) -> bool:
        """
        tells whether the token is expired
        """
        return datetime.now() - self.originally_issued > timedelta(seconds=self.expires_in)

    def check_scope(self, scope: str) -> bool:
        """
        check whether the current token's scope includes the given value
        """
        return scope.lower() in self.scope.split(" ")

    @classmethod
    def from_response(cls, response) -> 'Token':
        return cls(
            access_token=response["access_token"],
            expires_in=response["expires_in"],
            id_token=response["id_token"],
            scope=response["scope"],
            token_type=response["token_type"]
        )


EXAMPLE = {
    "access_token": "{access_token}",
    "expires_in": 2520,
    "id_token": False,
    "scope": "write offline_access",
    "token_type": "bearer"
}


class Tumblr:
    """
    Class representing the Tumblr API
    """
    consumer_id: str
    consumer_secret: str
    token: Token | None
    redirect_uri: str = environ.get("REDIRECT_URI")

    def __str__(self):
        return (
            f"<Tumblr API object | "
            f"consumer_id: '{self.consumer_id}', "
            f"token: '{self.token}', "
            f"redirect_uri: '{self.redirect_uri}'"
            ">"
        )

    default_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'PyTumblrBotKill/0.0.1',
    }

    def __init__(self):
        self.consumer_id = environ.get("TUMBLR_CONSUMER_KEY")
        self.consumer_secret = environ.get("TUMBLR_CONSUMER_SECRET")

    def authenticate(self, authentication_code):
        try:
            body = {
                'grant_type': 'authorization_code',
                'client_id': self.consumer_id,
                'client_secret': self.consumer_secret,
                'redirect_uri': self.redirect_uri,
                'code': authentication_code,
            }
            response = requests.post("https://api.tumblr.com/v2/oauth2/token",
                                     headers=self.default_headers, json=body)
            self.token = Token.from_response(response.json())
        except Exception:
            logging.error(response.content)

    @property
    def authenticated(self) -> bool:
        """
        checks whether the api object is authenticated
        """
        return self.token is not None and not self.token.expired
