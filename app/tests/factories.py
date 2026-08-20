import secrets

class Credentials:
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        userlen: int = 8,
        passlen: int = 12
    ):
        _username, _password = self.initialize(userlen=userlen, passlen=passlen)
        self.username = username or _username
        self.password = password or _password

    def as_dict(self):
        return {'username': self.username, 'password': self.password}

    @staticmethod
    def initialize(
        userlen: int = 8,
        passlen: int = 12
    ):
        # Generate pseudo-random hexadecimal string of length n
        return secrets.token_hex(userlen), secrets.token_hex(passlen)
