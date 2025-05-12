from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from mongo_orm.base_repository import BaseRepository
from db_methods_user_data_service.user_service import UserService
from db_methods_user_data_service.message_service import MessageService
from db_methods_user_data_service.group_service import GroupService
from authorization.security import TokenServiceImpl, EndpointsSecurityService
import settings
import datetime

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize services
token_service = TokenServiceImpl()
security_service = EndpointsSecurityService()

# Initialize repositories and services
user_repo = BaseRepository(settings.DB_CONNECTION_STRING, settings.DB_NAME, "users")
group_repo = BaseRepository(settings.DB_CONNECTION_STRING, settings.DB_NAME, "groups")
message_repo = BaseRepository(settings.DB_CONNECTION_STRING, settings.DB_NAME, "messages")

user_service = UserService(user_repo)
group_service = GroupService(group_repo)
message_service = MessageService(message_repo)

# Helper functions
def get_current_user(access_token):
    if not access_token or not token_service.verify(access_token):
        return None
    token_data = security_service.provide_encoded(access_token)
    return user_service.find_by_id(token_data['id'])

def require_auth(f):
    def decorated(*args, **kwargs):
        access_token = request.headers.get('accessToken')
        user = get_current_user(access_token)
        if not user:
            return jsonify({"message": "Authentication required"}), 401
        return f(user, *args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Authentication routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Invalid input"}), 400

    user = user_service.find_by_username(data['username'])
    if not user or user.get('password') != data['password']:
        return jsonify({"message": "Invalid credentials"}), 401

    token = token_service.encode(user['id'])
    user_service.update_status(user['id'], "online")
    
    return jsonify({
        **user,
        "token": token
    }), 200

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Invalid input"}), 400

    if user_service.find_by_username(data['username']):
        return jsonify({"message": "Username already exists"}), 409

    user = user_service.create_user(
        data['username'],
        data['password'],
        data.get('profile_pic', '')
    )
    token = token_service.encode(user['id'])
    
    return jsonify({
        **user,
        "token": token
    }), 201

# User routes
@app.route('/api/users/me', methods=['GET'])
@require_auth
def get_current_user_route(user):
    return jsonify(user), 200

@app.route('/api/users/me', methods=['PUT'])
@require_auth
def update_user_profile(user):
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid input"}), 400

    success = user_service.update_user(user['id'], data)
    if not success:
        return jsonify({"message": "Failed to update profile"}), 400

    updated_user = user_service.find_by_id(user['id'])
    return jsonify(updated_user), 200

# Group routes
@app.route('/api/groups', methods=['POST'])
@require_auth
def create_group(user):
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"message": "Group name is required"}), 400

    group = group_service.create_group(
        data['name'],
        user['id'],
        data.get('is_private', False),
        data.get('password', '')
    )
    return jsonify(group), 201

@app.route('/api/groups', methods=['GET'])
@require_auth
def get_user_groups(user):
    groups = group_service.get_user_groups(user['id'])
    return jsonify(groups), 200

@app.route('/api/groups/<group_id>', methods=['GET'])
@require_auth
def get_group(user, group_id):
    if not group_service.is_member(group_id, user['id']):
        return jsonify({"message": "Not a member of this group"}), 403

    group = group_service.get_group(group_id)
    if not group:
        return jsonify({"message": "Group not found"}), 404

    return jsonify(group), 200

@app.route('/api/groups/<group_id>/members', methods=['POST'])
@require_auth
def add_group_member(user, group_id):
    if not group_service.is_admin(group_id, user['id']):
        return jsonify({"message": "Not authorized"}), 403

    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"message": "User ID is required"}), 400

    success = group_service.add_member(group_id, data['user_id'])
    if not success:
        return jsonify({"message": "Failed to add member"}), 400

    return jsonify({"message": "Member added successfully"}), 200

@app.route('/api/groups/<group_id>/members/<member_id>', methods=['DELETE'])
@require_auth
def remove_group_member(user, group_id, member_id):
    if not group_service.is_admin(group_id, user['id']):
        return jsonify({"message": "Not authorized"}), 403

    success = group_service.remove_member(group_id, member_id)
    if not success:
        return jsonify({"message": "Failed to remove member"}), 400

    return jsonify({"message": "Member removed successfully"}), 200

# Message routes
@app.route('/api/groups/<group_id>/messages', methods=['GET'])
@require_auth
def get_group_messages(user, group_id):
    if not group_service.is_member(group_id, user['id']):
        return jsonify({"message": "Not a member of this group"}), 403

    before = request.args.get('before')
    if before:
        try:
            before = datetime.datetime.fromisoformat(before)
        except:
            return jsonify({"message": "Invalid date format"}), 400

    messages = message_service.get_group_messages(
        group_id,
        limit=int(request.args.get('limit', 50)),
        before=before
    )
    return jsonify(messages), 200

@app.route('/api/groups/<group_id>/messages', methods=['POST'])
@require_auth
def send_message(user, group_id):
    if not group_service.is_member(group_id, user['id']):
        return jsonify({"message": "Not a member of this group"}), 403

    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"message": "Message content is required"}), 400

    message = message_service.create_message(
        user['id'],
        group_id,
        data['content'],
        data.get('type', 'text')
    )
    
    # Emit the message to all group members
    socketio.emit('new_message', message, room=group_id)
    
    return jsonify(message), 201

# WebSocket events
@socketio.on('connect')
def handle_connect():
    access_token = request.args.get('token')
    user = get_current_user(access_token)
    if not user:
        return False
    
    user_service.update_status(user['id'], "online")
    emit('status_change', {'user_id': user['id'], 'status': 'online'}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    access_token = request.args.get('token')
    user = get_current_user(access_token)
    if user:
        user_service.update_status(user['id'], "offline")
        emit('status_change', {'user_id': user['id'], 'status': 'offline'}, broadcast=True)

@socketio.on('join_group')
def handle_join_group(data):
    access_token = request.args.get('token')
    user = get_current_user(access_token)
    if not user:
        return
    
    group_id = data.get('group_id')
    if group_service.is_member(group_id, user['id']):
        join_room(group_id)
        emit('user_joined', {'user_id': user['id']}, room=group_id)

@socketio.on('leave_group')
def handle_leave_group(data):
    access_token = request.args.get('token')
    user = get_current_user(access_token)
    if not user:
        return
    
    group_id = data.get('group_id')
    if group_service.is_member(group_id, user['id']):
        leave_room(group_id)
        emit('user_left', {'user_id': user['id']}, room=group_id)

@socketio.on('typing')
def handle_typing(data):
    access_token = request.args.get('token')
    user = get_current_user(access_token)
    if not user:
        return
    
    group_id = data.get('group_id')
    if group_service.is_member(group_id, user['id']):
        emit('user_typing', {
            'user_id': user['id'],
            'username': user['username']
        }, room=group_id)

if __name__ == '__main__':
    socketio.run(app, debug=True)