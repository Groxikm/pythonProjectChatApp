from flask_cors import CORS
from mongo_orm import mongo_db
from flask import Flask, request

from authorization.security import TokenServiceImpl, EndpointsSecurityService

from db_methods_user_data_service import service as service_user_data
from db_methods_user_data_service.messages_data_service import service as service_mes_data
from db_methods_user_data_service.groups_data_service import service as service_groups_data
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
        mongo_db.MongoRepository(settings.DB_CONNECTION_STRING, settings.DB_NAME, "user_data_collection"))
"""
            "id": self.get_id_str(),
            "globalRole": self.get_global_role(),
            "username": self.username,
            "email": self.email,
            "profilePicture": self.profilePicture,
            "password": self.password,
            "status": self.status,
            "friends": self.friends, # list []
            "lastActive": self.lastActive.strftime(DATE_FORMAT), # date format YYYY-MM-DD
            "date": self.date.strftime(DATE_FORMAT) # date format YYYY-MM-DD
"""
user_group_service = service_groups_data.GroupsDataService(
    mongo_db.MongoRepository(settings.DB_CONNECTION_STRING, settings.DB_NAME, "user_rooms_attempts"))
"""
            self.id = id
            self.creator_id = creator_id
            self.participants = participants
            self.password = password
            self.admins = admins
"""

user_message_service = service_mes_data.MessagesDataService(
    mongo_db.MongoRepository(settings.DB_CONNECTION_STRING, settings.DB_NAME, "messages_collection"))
"""
        self.id = id
        self.user_id = user_id
        self.room_id = room_id
        self.location = location
        self.status = status
        self.role = role
        self.date = date

"""


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
                    "global_role": user_data.global_role,
                    "username": user_data.username,
                    "password": user_data.password,
                    "profile_pic": user_data.profile_pic,
                    "status": user_data.status,
                    "friends" : user_data.friends,
                    "last_active_date" : user_data.last_active_date,
                    "date" : user_data.date
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
                "global_role": user_data.global_role,
                "username": user_data.username,
                "password": user_data.password,
                "profile_pic": user_data.profile_pic,
                "status": user_data.status,
                "friends": user_data.friends,
                "last_active_date": user_data.last_active_date,
                "date": user_data.date
            }
            return user_info, 200
        elif not user_data:
            return {"message": "User not found"}, 404
        else:
            return {"message": "Invalid password"}, 401

    except Exception as e:
        return {"message": "An error occurred during login", "error": str(e)}, 400


@app.route('/api/add-user', methods=['POST'])
def add_user():
    # security check via token
    verification_result = security_service.secure_user(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    data = request.get_json()
    try:
        # expected from request fields are addressing to the received data
        user_create_dto = {
            "username": data.username,
            "profile_pic": data.profile_pic,
            "status": None,
            "friends": []  # list []
        }
        try:
            user_data_service.find_by_login(user_create_dto['username'])
        except Exception as e:
            created_user = user_data_service.add_new(user_create_dto)
            return created_user.to_web_dto(), 201

        return {"error": "User not created. Provided name and surname already exists"}, 400
    except Exception as e:
        return {"error": str(e)}, 400


@app.route('/api/user-reg-attempt', methods=['POST'])
def add_group():
    # security check via token
    verification_result = security_service.secure_user(request.headers.get('accessToken'))
    if verification_result is not None:
        return {"message": "Invalid token!"}, 401

    data = request.get_json()
    try:
        # expected from request fields are addressing to the received data
        group_create_dto = {
            "username": data.username,
            "profile_pic": data.profile_pic,
            "status": None,
            "friends": []  # list []
        }
        try:
            user_data_service.find_by_login(group_create_dto['username'])
        except Exception as e:
            created_user = user_data_service.add_new(group_create_dto)
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
            updated_user_data.username = data['username']
        except Exception as e:
            message["errorUserName"] = str(e)

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


if __name__ == '__main__':
    app.run()
