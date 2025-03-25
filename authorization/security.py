import jwt
import datetime
from datetime import timedelta
import settings


class TokenServiceImpl:

    def __init__(self) -> None:
        self._SECRET_KEY = settings.SECRET_KEY

    def verify(self, token: str) -> bool:
        try:
            decoded = jwt.decode(token, self._SECRET_KEY, algorithms=["HS256"])
            exp = datetime.datetime.strptime(decoded['expiration'], "%m/%d/%Y_%H:%M:%S")
            if datetime.datetime.now() > exp:
                return False
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

    def verify_user(self, token: str) -> bool:
        try:
            decoded = jwt.decode(token, self._SECRET_KEY, algorithms=["HS256"])
            if decoded['role'] != "USER":
                return False
            exp = datetime.datetime.strptime(decoded['expiration'], "%m/%d/%Y_%H:%M:%S")
            if datetime.datetime.now() > exp:
                return False
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

    def verify_admin(self, token: str) -> bool:
        try:
            decoded = jwt.decode(token, self._SECRET_KEY, algorithms=["HS256"])
            if decoded['role'] != "ADMIN":
                return False
            exp = datetime.datetime.strptime(decoded['expiration'], "%m/%d/%Y_%H:%M:%S")
            if datetime.datetime.now() > exp:
                return False
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

    def encode(self, role: str, user_id: str) -> str:
        expiration = datetime.datetime.now() + timedelta(1, 300)
        payload = {
            'role': role,
            'id': user_id,
            'expiration': expiration.strftime("%m/%d/%Y_%H:%M:%S")
        }
        token = jwt.encode(payload, self._SECRET_KEY, algorithm="HS256")
        return token


class ErrorMessage:
    def __init__(self, message: str) -> None:
        self._message = message


    def get_dto(self) -> dict:
        return {
            "error-message": self._message
        }


class EndpointsSecurityService:
    def __init__(self) -> None:
        self._service = TokenServiceImpl()
        self._SECRET_KEY = settings.SECRET_KEY
        self.status_rules = {}

    def set_status_rules(self, rules) -> None:
        # print(rules)
        self.status_rules = rules

    def get_status_rules(self) -> dict:
        return self.status_rules

    def verify(self, token: str) -> dict | None:
        encoding = self._service.verify(token)
        if not encoding:
            return ErrorMessage("token invalid").get_dto()
        return None

    def secure_user(self, token: str) -> dict | None:
        encoding = self._service.verify_user(token)
        if not encoding:
            return ErrorMessage("token invalid").get_dto()
        return None

    def secure_admin(self, token: str) -> dict | None:
        encoding = self._service.verify_admin(token)
        if not encoding:
            return ErrorMessage("token invalid").get_dto()
        return None

    # method to access encoded contents of the token
    def provide_encoded(self, token: str) -> dict:
        try:
            decoded = jwt.decode(token, self._SECRET_KEY, algorithms=["HS256"])
            return {"id": decoded['id'], "role": decoded['role']}
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

    def valid_user_status_check(self, freq, backlog) -> str:
        f_check = self.frequency_check(freq)
        b_check = self.backlog_check(backlog)

        if f_check and not b_check:
            return "Orange b"
        if not f_check and b_check:
            return "Orange f"
        if f_check and b_check:
            return "Green"

        return "Red"

    def frequency_calc(self, user_days) -> int:
        return int( float(user_days) * 100  / float(self.status_rules['days_scope'])  )

    def frequency_check(self, user_days: int) -> bool:
        try:
            # days limit is value of how many days should be counted as visits
            user_freq = user_days # self.frequency_calc(user_days)

            if self.status_rules['attendance'] < user_freq:
                return True
        except Exception as e:
            print(e)

        return False

    def backlog_check(self, backlog: int) -> bool:
        try:
            # meaning there are unpaid months, backlog
            if backlog <= self.status_rules['backlog_limit']:
                return True
        except Exception as e:
            print(e)

        return False

    # date check presents just in case needed
    def date_check(self, valid_due: datetime) -> bool:
        try:
            if datetime.datetime.now() < valid_due:
                return True
        except Exception as e:
            print(e)

        return False

