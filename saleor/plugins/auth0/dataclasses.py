from dataclasses import dataclass


@dataclass
class Auth0Config:
    client_id: str
    client_secret: str
    enable_refresh_token: bool
    domain: str
