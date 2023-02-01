import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from os import environ
import logging
from typing import Optional

import requests


class RateLimitException(Exception):
    pass


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
        object.__setattr__(self, "originally_issued", datetime.now().replace(tzinfo=None))

    @property
    def expired(self) -> bool:
        """
        tells whether the token is expired
        """
        return datetime.now().replace(tzinfo=None) - self.originally_issued.replace(tzinfo=None) > timedelta(seconds=self.expires_in)

    def check_scope(self, scope: str) -> bool:
        """
        check whether the current token's scope includes the given value
        """
        return scope.lower() in self.scope.split(" ")

    @classmethod
    def from_dict(cls, response) -> 'Token':
        created = cls(
            access_token=response["access_token"],
            expires_in=response["expires_in"],
            id_token=response["id_token"],
            scope=response["scope"],
            token_type=response["token_type"]
        )
        if response.get("originally_issued") is not None:
            object.__setattr__(created, "originally_issued", response["originally_issued"])
        return created

    def to_dict(self):
        return {
            "access_token": self.access_token,
            "expires_in": self.expires_in,
            "id_token": self.id_token,
            "scope": self.scope,
            "token_type": self.token_type,
            "originally_issued": self.originally_issued,
        }


EXAMPLE = {
    "access_token": "{access_token}",
    "expires_in": 2520,
    "id_token": False,
    "scope": "write",
    "token_type": "bearer"
}

@dataclass
class Blog:
    avatar: str
    follower_count: int
    name: str
    description: str
    primary: bool
    background_color: str
    header: str
    text_color: str
    title: str
    url: str
    uuid: str

    @classmethod
    def from_json(cls, json):
        return cls(
            avatar=json["avatar"][0]["url"],
            follower_count=json["followers"],
            name=json["name"],
            description=json["description"],
            primary=json["primary"],
            background_color=json["theme"].get("background_color"),
            header=json["theme"].get("header_image"),
            text_color=json["theme"].get("title_color"),
            title=json["title"],
            url=json["url"],
            uuid=json["uuid"],
        )

class Tumblr:
    """
    Class representing the Tumblr API
    """
    consumer_id: str
    consumer_secret: str
    token: Optional[Token]
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

    def __init__(self, token=None):
        self.consumer_id = environ.get("TUMBLR_CONSUMER_KEY")
        self.consumer_secret = environ.get("TUMBLR_CONSUMER_SECRET")
        if token is not None:
            self.token = Token.from_dict(token)
        else:
            self.token = None

    def authenticate(self, authentication_code):
        body = {
            'grant_type': 'authorization_code',
            'code': authentication_code,
            'client_id': self.consumer_id,
            'client_secret': self.consumer_secret,
            'redirect_uri': environ.get("REDIRECT_URI")
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'PyTumblrBotKill/0.0.1',
        }
        logging.error(f"authenticating with {authentication_code}")
        response = requests.post("https://api.tumblr.com/v2/oauth2/token",
                                 headers=headers, json=body)
        logging.error(str(response.json()))
        self.token = Token.from_dict(response.json())

    @property
    def authenticated(self) -> bool:
        """
        checks whether the api object is authenticated
        """
        return self.token is not None and not self.token.expired

    def get(self, endpoint):
        """
        perform an http GET
        """
        response = requests.get(f"https://api.tumblr.com/v2/{endpoint}", headers=self.privileged_headers)
        return response.json()


    def post(self, endpoint, body):
        response = requests.post(f"https://api.tumblr.com/v2/{endpoint}", headers=self.privileged_headers, json=body)
        return response.json()


    def user_info(self):
        """
        get the authenticated user's info
        """
        return self.get("user/info")["response"]["user"]

    def user_blogs(self):
        """
        get a list of Blog objects
        """
        return [Blog.from_json(b) for b in self.user_info()["blogs"]]

    def blog_followers(self, blog: Blog):
        resp = self.get(f"blog/{blog.uuid}/followers")
        users = resp["response"]["users"]
        return users

    def public_blog_post_count(self, blog_name: str):
        resp = self.get(f"blog/{blog_name}/info?fields[blogs]=posts,avatar")
        return resp["response"]["blog"]["posts"], resp["response"]["blog"]["avatar"]

    @property
    def privileged_headers(self):
        headers = self.default_headers
        headers.update({"Authorization": f"Bearer {self.token.access_token}"})
        return headers
