from flask_cors import CORS
from mongo_orm import mongo_db
from flask import Flask, request

from authorization.security import TokenServiceImpl, EndpointsSecurityService

from db_methods_user_data_service import service as service_user_data
from db_methods_user_data_service.registration_data_service import service as service_reg_data
from db_methods_user_data_service.condition_service import service as service_status_condition
import settings
app = Flask(__name__)
CORS(app)

# token service uses jwt token lib to manipulate tokens
token_service = TokenServiceImpl()
# security service addresses token service to represent information from tokens
security_service = EndpointsSecurityService()

# data service are to provide convenient data representaion for the DB and python
# as well as implies security measures for example by not returning password
user_data_service = service_user_data.UserDataService(
        mongo_db.MongoRepository(settings.DB_CONNECTION_STRING, "QR_code_app_DB", "user_data_collection"))
"""
            "id": self.get_id_str(),
            "club": self.club,
            "role": self.role,
            "name": self.name,
            "surname": self.surname,
            "login": self.login,
            "password": self.password,
            "visit_frequency": self.visit_frequency,
            "backlog": self.backlog,
            "club_link": self.avatar_link,
            "avatar_link": self.avatar_link,
            "date": self.date.strftime(DATE_FORMAT)
"""
user_reg_service = service_reg_data.RegistrationDataService(
    mongo_db.MongoRepository(settings.DB_CONNECTION_STRING, "QR_code_app_DB", "user_registration_attempts"))
"""
            "id": self.get_id_str(),
            "user_id": self.user_id,
            "location": self.location,
            "status": self.status,
            "role": self.role,
            "date": self.date.strftime(DATE_FORMAT)
"""
status_condition_service = service_status_condition.ConditionDataService(
        mongo_db.MongoRepository(settings.DB_CONNECTION_STRING, "QR_code_app_DB", "condition_collection"))
"""
            "id": self.get_id_str(),
            "days_scope": self.days_scope,
            "days_limit": self.days_limit,
            "attendance": self.attendance,
            "backlog_limit": self.backlog_limit
"""


def update_status_check_rules():
    try:
        status_rules_json = status_condition_service.find_by_id(settings.GENERAL_STATUS_RULES_ID)
        # print(status_rules_json.to_web_dto())
        security_service.set_status_rules(status_rules_json.to_web_dto())
    except Exception as e:
        print(e)


# setting status rules at the server start
update_status_check_rules()


@app.route('/login', methods=['POST'])
def login():
    # first action is to process login via token
    isTokenValid = False
    try:
        received_token = request.headers.get('accessToken')
        isTokenValid = token_service.verify(received_token)
        if isTokenValid:
            token_data = security_service.provide_encoded(received_token)
            user_data = user_data_service.find_by_id(token_data['id'])
            if token_service.verify_admin(received_token):
                user_info = {
                    "id": user_data.id,
                    "name": user_data.name,
                    "surname": user_data.surname,
                    "accessToken": received_token,
                    "avatar_link": user_data.avatar_link,
                    "role": user_data.role
                }
                return user_info, 200
    except Exception as e:
        isTokenValid = False

    # second action process login in ordinary way
    # login logic when the received token didn't pass
    data = request.get_json()
    if not data or 'login' not in data or 'password' not in data:
        return {"message": "Invalid input"}, 400

    login_user = data['login']
    password = data['password']
    try:
        user_data = user_data_service.find_by_login(login_user)
        if user_data and user_data.password == password:
            try:
                token_login = token_service.encode(user_data.role, user_data.id)
            except Exception as e:
                return {"message": str(e)}, 400

            # Return user_info as allowed fragment of user_data
            user_info = {
                "id": user_data.id,
                "name": user_data.name,
                "surname": user_data.surname,
                "accessToken": token_login,
                "avatar_link": user_data.avatar_link,
                "role": user_data.role

            }
            return user_info, 200
        elif not user_data:
            return {"message": "User not found"}, 404
        else:
            return {"message": "Invalid password"}, 401

    except Exception as e:
        return {"message": "An error occurred during login", "error": str(e)}, 400


@app.route('/api/user-reg-attempt', methods=['POST'])
def add_registration_attempt():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    data = request.get_json()
    user_id = data['id']
    user_loc = data['location']

    try:
        # handling question whether the user with the id exists
        user = user_data_service.find_by_id(user_id)
        status = security_service.valid_user_status_check(user.visit_frequency, user.backlog)
        user_data = {
            "user_id": user_id,
            "location": user_loc,
            "status": status,
            "role": user.role
        }
        user_reg_service.add_new(user_data)
        return {"message": "User registered!", "user_id": user_id, "status": status}, 200
    except Exception as e:
        return {"error": str(e)}, 400


@app.route('/api/user-reg-attempt-green', methods=['POST'])
def add_registration_attempt_green():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    data = request.get_json()
    user_id = data['id']
    user_loc = data['location']

    try:
        # handling question whether the user with the id exists
        user = user_data_service.find_by_id(user_id)
        status = security_service.valid_user_status_check(user.visit_frequency, user.backlog)
        if status == "Green":
            user_data = {
                "user_id": user_id,
                "location": user_loc,
                "status": status,
                "role": user.role
            }
            user_reg_service.add_new(user_data)
            return {"message": "User registered!", "user_id": user_id, "status": status}, 200
        return {"message": "User status is not Green!", "user_id": user_id, "status": status}, 200
    except Exception as e:
        return {"error": str(e)}, 400


@app.route('/api/add-user', methods=['POST'])
def add_user():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    data = request.get_json()
    try:
        # expected from request fields are addressing to the received data
        user_create_dto = {
            "club": data['club'],
            "team": data['team'],
            "name": data['name'],
            "surname": data['surname'],
            "login": data['login'],
            "password": data['password'],
            "visit_frequency": 0,
            "backlog": 0,
            "role": "USER",
            "club_link": data['club_link'],
            "avatar_link": data['avatar_link']
        }
        try:
            user_data_service.find_by_name_surname(user_create_dto['name'], user_create_dto['surname'])
            user_data_service.find_by_login(user_create_dto['login'])
        except Exception as e:
            created_user = user_data_service.add_new(user_create_dto)
            return created_user.to_web_dto(), 201

        return {"error": "User not created. Provided name and surname already exists"}, 400
    except Exception as e:
        return {"error": str(e)}, 400


@app.route('/api/find-user-by-id', methods=['GET'])
def find_user_by_id():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    user_id = request.args.get('id')
    try:
        user_data = user_data_service.find_by_id(user_id).to_web_dto()
        user_data['attendance'] = security_service.frequency_calc(user_data['visit_frequency'])
        return user_data, 200
    except Exception as e:
        return {"error": str(e)}, 400


@app.route('/api/find-rules', methods=['GET'])
def find_rules_by_id():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    rules_id = settings.GENERAL_STATUS_RULES_ID
    try:
        rules_data = status_condition_service.find_by_id(rules_id).to_web_dto()
        return rules_data, 200
    except Exception as e:
        return {"error": str(e)}, 400


@app.route('/api/find-user-by-name-surname', methods=['GET'])
def find_user_by_name_surname():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    user_name = request.args.get('name')
    user_surname = request.args.get('surname')
    try:
        user_data = user_data_service.find_by_name_surname(user_name, user_surname)

        return user_data.to_web_dto(), 200
    except Exception as e:
        return {"error": str(e)}, 400


# User change endpoints
@app.route('/api/change-user-data', methods=['PUT'])
def change_user_data():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    data = request.get_json()
    user_id = data['id']
    message = {}
    try:
        updated_user_data = user_data_service.find_by_id(user_id)
        password = updated_user_data.password

        try:
            updated_user_data.name = data['name']
        except Exception as e:
            message["errorName"] = str(e)

        try :
            updated_user_data.surname = data['surname']
        except Exception as e:
            message["errorSurname"] = str(e)

        try:
            updated_user_data.avatar_link = data['avatar_link']
        except Exception as e:
            message["errorAvatar"] = str(e)

        try:
            updated_user_data.visit_frequency = data['visit_frequency']
        except Exception as e:
            message["errorVF"] = str(e)

        try:
            updated_user_data.backlog = data['backlog']
        except Exception as e:
            message["errorBL"] = str(e)

        user_data_dto_with_password = updated_user_data.to_web_dto()
        user_data_dto_with_password['password'] = password

        user_data_service.update(user_data_dto_with_password)
        return {"message": "User data changed!", "changeReport": message}, 200
    except Exception as e:
        return {"error": str(e)}, 400


# User change endpoints
@app.route('/api/change-status-rules', methods=['PUT'])
def change_status_rules():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    data = request.get_json()
    try:
        updated_rules = status_condition_service.find_by_id(settings.GENERAL_STATUS_RULES_ID).to_web_dto()

        updated_rules['days_scope'] = updated_rules['days_scope']
        updated_rules['days_limit'] = updated_rules['days_limit'] # this field is so far not in use
        updated_rules['attendance'] = int(data['attendance'])
        updated_rules['backlog_limit'] = int(data['backlog_limit'])
        status_condition_service.update(updated_rules)
        # important rules update in the app
        update_status_check_rules()
        return {"message": "Status rules changed!"}, 200
    except Exception as e:
        return {"error": str(e)}, 400


@app.route('/api/delete-user-by-id', methods=['PUT'])
def delete_user_by_id():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    user_id = request.args.get('id')
    user_data = user_data_service.find_by_id(user_id)
    if user_data.role == "ADMIN":
        return {"error": "User can't be deleted"}, 400
    try:
        user_data_service.delete(user_id)
        return {"message": "User deleted!", "id": user_id}, 200
    except Exception as e:
        return {"error": str(e)}, 400


# Log getting endpoints
@app.route('/api/find-user-reg-attempts', methods=['GET'])
def find_user_reg_attempts():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit'))
    latest_date = request.args.get('latest_date')
    last_attempts_dtos = []
    try:
        user_data_service.find_by_id(user_id)
        last_attempts = user_reg_service.find_all_by_id(latest_date, limit, user_id)
        for attempt in last_attempts:
            last_attempts_dtos.append(attempt.to_web_dto())
        last_users_dto = {
            "userId": user_id,
            "attempts": last_attempts_dtos,
            "latestDate": last_attempts_dtos[-1]["date"]
        }
        return last_users_dto, 200
    except Exception as e:
        return {"error": "No more logs exist", "server": str(e)}, 204


@app.route('/api/find-all-reg-attempts', methods=['GET'])
def find_all_reg_attempts():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    limit = int(request.args.get('limit'))
    latest_date = request.args.get('last_date')
    last_attempts_dtos = []
    try:
        last_attempts = user_reg_service.find_all_by_page(latest_date, limit)
        for attempt in last_attempts:
            last_attempts_dtos.append(attempt.to_web_dto())
        last_users_dto = {
            "attempts": last_attempts_dtos,
            "latestDate": last_attempts_dtos[-1]["date"]
        }
        return last_users_dto, 200
    except Exception as e:
        return {"error": "No more logs exist", "server": str(e)}, 204


@app.route('/api/get-users', methods=['GET'])
def get_users():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    last_date = request.args.get('last_date')
    limit = int(request.args.get('limit'))
    last_users_dtos = []
    try:

        last_users = user_data_service.find_all_by_page(last_date, limit)

        for user in last_users:
            last_users_dtos.append(user.to_web_dto())

        last_users_dto = {
            "last_date": last_users_dtos[-1]["date"],
            "users": last_users_dtos,
        }
        return last_users_dto, 200
    except Exception as e:
        return {"error": "No more logs exist", "server": str(e)}, 204


@app.route('/api/check-validity', methods=['GET'])
def check_validity_by_id():
    # security check via token
    verification_result = security_service.secure_admin(request.headers.get('accessToken'))
    if verification_result is not None:
        verification_result = security_service.secure_user(request.headers.get('accessToken'))
        if verification_result is not None:
            return {"message": "Invalid token!"}, 401

    user_id = request.args.get('id')
    try:
        user_data = user_data_service.find_by_id(user_id)
        valid_status = security_service.valid_user_status_check(user_data.visit_frequency, user_data.backlog)
        return {"status": valid_status}, 200
    except Exception as e:
        return {"error": str(e)}, 400


if __name__ == '__main__':
    app.run()
