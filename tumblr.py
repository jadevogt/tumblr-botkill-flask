from dataclasses import dataclass



@dataclass
class Token:
    """ tumblr auth token """
    error: str
    error_description: str
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str


class Tumblr:
    def __init__(self):
        pass
