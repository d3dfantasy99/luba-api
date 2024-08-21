from datetime import datetime
from dataclasses import dataclass

@dataclass
class MammotionAccount:
    id: int
    email: str
    password: str
    bearerToken: str
    refreshToken: str
    authorization_code: str
    expires_in: int
    areaCode: str
    userAccount: str
