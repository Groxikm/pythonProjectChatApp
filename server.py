from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from services.base_repository import BaseRepository
from services.user_service import UserService
from services.message_service import MessageService
from services.group_service import GroupService
from services.log_service import LogService
import settings
import datetime
from typing import Dict, Set
import traceback
from bson import ObjectId

app = Flask(__name__)
# Use a simple, permissive CORS configuration for development
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize repositories and services with error handling
try:
    user_repo = BaseRepository(settings.DB_CONNECTION_STRING, settings.DB_NAME, "users")
    group_repo = BaseRepository(settings.DB_CONNECTION_STRING, settings.DB_NAME, "groups")
    message_repo = BaseRepository(settings.DB_CONNECTION_STRING, settings.DB_NAME, "messages")
    log_repo = BaseRepository(settings.DB_CONNECTION_STRING, settings.DB_NAME, "logs")

    user_service = UserService(user_repo)
    group_service = GroupService(group_repo)
    message_service = MessageService(message_repo)
    log_service = LogService(log_repo)
    
    # Test the connection
    user_repo.count()
    print("✓ Successfully connected to MongoDB")
    
except Exception as e:
    print(f"✗ Failed to connect to MongoDB: {e}")
    print("⚠️  Server will start but database operations will fail")
    # Create dummy services to prevent crashes
    user_service = None
    group_service = None
    message_service = None
    log_service = None

# Track connected users
connected_users: Dict[str, str] = {}  # socket_id -> user_id
user_sockets: Dict[str, Set[str]] = {}  # user_id -> set of socket_ids

# =============================================================================
# FAVICON ROUTE
# =============================================================================

@app.route('/favicon.ico')
def favicon():
    """Return a simple response for favicon requests to prevent 404 errors"""
    return '', 204

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Use global variables properly
        if 'user_service' in globals() and user_service is not None:
            # Try to perform a simple database operation
            user_service.repository.count()
            db_status = "connected"
        else:
            db_status = "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return jsonify({
        "status": "running",
        "database": db_status,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }), 200

# =============================================================================
# DATABASE CONNECTION CHECK DECORATOR
# =============================================================================

def require_db_connection(f):
    """Decorator to check if database connection is available"""
    def wrapper(*args, **kwargs):
        if not user_service or not group_service or not message_service:
            return jsonify({"error": "Database connection not available"}), 503
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# =============================================================================
# LOGGING MIDDLEWARE
# =============================================================================

@app.after_request
def log_request(response):
    """Log successful requests to the database"""
    # Don't log preflight OPTIONS requests, as they shouldn't have side effects
    if request.method == 'OPTIONS':
        return response
    
    if response.status_code < 400 and log_service:
        try:
            log_service.create_log(
                message=f"{request.method} {request.path} - {response.status}",
                url=request.url,
                level="INFO",
                extra_data={
                    "request_ip": request.remote_addr,
                    "response_status": response.status_code,
                }
            )
        except Exception as e:
            print(f"Failed to log request: {e}")
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle and log unhandled exceptions"""
    tb_str = traceback.format_exc()
    
    # Try to log the exception to the database, but don't let logging break the error handler
    if log_service:
        try:
            log_service.create_log(
                message=f"Unhandled Exception: {str(e)}",
                url=request.url,
                level="ERROR",
                extra_data={
                    "request_ip": request.remote_addr,
                    "traceback": tb_str
                }
            )
        except Exception as log_e:
            print(f"CRITICAL: Failed to log exception to database: {log_e}")

    # Also log to console for immediate visibility, regardless of DB status
    print(f"Exception occurred: {tb_str}")
    
    response = jsonify({
        "error": "Internal Server Error",
        "message": str(e)
    })
    response.status_code = 500
    return response

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def emit_to_user(user_id: str, event: str, data: dict):
    """Emit an event to all sockets of a specific user"""
    if user_id in user_sockets:
        for socket_id in user_sockets[user_id]:
            socketio.emit(event, data, room=socket_id)

def emit_to_group_members(group_id: str, event: str, data: dict, exclude_user: str = None):
    """Emit an event to all members of a group"""
    members = group_service.get_group_members(group_id)
    for member_id in members:
        if member_id != exclude_user:
            emit_to_user(member_id, event, data)

# =============================================================================
# REST API ENDPOINTS
# =============================================================================

@app.route('/api/users/register', methods=['POST'])
@require_db_connection
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        profile_pic = data.get('profile_pic', '')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        user = user_service.create_user(username, password, profile_pic)
        return jsonify({"message": "User created successfully", "user": user}), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/users/login', methods=['POST'])
@require_db_connection
def login():
    """Login user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        user = user_service.authenticate_user(username, password)
        if user:
            return jsonify({"message": "Login successful", "user": user}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
            
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/users/<user_id>', methods=['GET'])
@require_db_connection
def get_user(user_id):
    """Get user by ID"""
    try:
        # Validate that user_id is not undefined or invalid
        if not user_id or user_id == 'undefined':
            return jsonify({"error": "Invalid user_id provided"}), 400
        
        # Validate ObjectId format
        try:
            ObjectId(user_id)
        except Exception:
            return jsonify({"error": "Invalid user_id format"}), 400
        
        user = user_service.find_by_id(user_id)
        if user:
            return jsonify(user), 200
        return jsonify({"error": "User not found"}), 404
        
    except Exception as e:
        print(f"Error in get_user: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
@require_db_connection
def update_user(user_id):
    """Update user data"""
    try:
        data = request.get_json()
        success = user_service.update_user(user_id, data)
        if success:
            user = user_service.find_by_id(user_id)
            return jsonify({"message": "User updated", "user": user}), 200
        return jsonify({"error": "Update failed"}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/users/<user_id>/friends', methods=['GET'])
@require_db_connection
def get_friends(user_id):
    """Get user's friends"""
    friends = user_service.get_friends(user_id)
    return jsonify(friends), 200

@app.route('/api/users/<user_id>/friends/<friend_id>', methods=['POST'])
@require_db_connection
def add_friend(user_id, friend_id):
    """Add a friend"""
    success = user_service.add_friend(user_id, friend_id)
    if success:
        return jsonify({"message": "Friend added"}), 200
    return jsonify({"error": "Failed to add friend"}), 400

@app.route('/api/users/<user_id>/friends/<friend_id>', methods=['DELETE'])
@require_db_connection
def remove_friend(user_id, friend_id):
    """Remove a friend"""
    success = user_service.remove_friend(user_id, friend_id)
    if success:
        return jsonify({"message": "Friend removed"}), 200
    return jsonify({"error": "Failed to remove friend"}), 400

@app.route('/api/users/search', methods=['GET'])
@require_db_connection
def search_users():
    """Search users by username"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    users = user_service.search_users(query, limit)
    return jsonify(users), 200

@app.route('/api/users/online', methods=['GET'])
@require_db_connection
def get_online_users():
    """Get all online users"""
    users = user_service.get_online_users()
    return jsonify(users), 200

# =============================================================================
# GROUP ENDPOINTS
# =============================================================================

@app.route('/api/groups', methods=['POST'])
@require_db_connection
def create_group():
    """Create a new group"""
    try:
        data = request.get_json()
        name = data.get('name')
        creator_id = data.get('creator_id')
        description = data.get('description', '')
        is_private = data.get('is_private', False)
        
        if not name or not creator_id:
            return jsonify({"error": "Name and creator_id required"}), 400
        
        group = group_service.create_group(name, creator_id, description, is_private)
        return jsonify({"message": "Group created", "group": group}), 201
        
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/groups/<group_id>', methods=['GET'])
@require_db_connection
def get_group(group_id):
    """Get group details"""
    try:
        # Validate that group_id is not undefined or invalid
        if not group_id or group_id == 'undefined':
            return jsonify({"error": "Invalid group_id provided"}), 400
        
        # Validate ObjectId format
        try:
            ObjectId(group_id)
        except Exception:
            return jsonify({"error": "Invalid group_id format"}), 400
        
        group = group_service.get_group(group_id)
        if group:
            return jsonify(group), 200
        return jsonify({"error": "Group not found"}), 404
        
    except Exception as e:
        print(f"Error in get_group: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/groups/<group_id>', methods=['PUT'])
@require_db_connection
def update_group(group_id):
    """Update group details"""
    try:
        data = request.get_json()
        requester_id = data.get('requester_id')
        
        if not requester_id:
            return jsonify({"error": "requester_id required"}), 400
        
        success = group_service.update_group(group_id, data, requester_id)
        if success:
            group = group_service.get_group(group_id)
            return jsonify({"message": "Group updated", "group": group}), 200
        return jsonify({"error": "Update failed or insufficient permissions"}), 400
        
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/groups/<group_id>/members/<user_id>', methods=['POST'])
@require_db_connection
def join_group(group_id, user_id):
    """Join a group"""
    try:
        # Validate that group_id and user_id are not undefined or invalid
        if not group_id or group_id == 'undefined':
            return jsonify({"error": "Invalid group_id provided"}), 400
        
        if not user_id or user_id == 'undefined':
            return jsonify({"error": "Invalid user_id provided"}), 400
        
        # Validate ObjectId format
        try:
            ObjectId(group_id)
        except Exception:
            return jsonify({"error": "Invalid group_id format"}), 400
        
        try:
            ObjectId(user_id)
        except Exception:
            return jsonify({"error": "Invalid user_id format"}), 400
        
        success = group_service.add_member(group_id, user_id)
        if success:
            # Notify group members
            emit_to_group_members(group_id, 'user_joined', {
                'group_id': group_id,
                'user_id': user_id
            })
            return jsonify({"message": "Joined group"}), 200
        return jsonify({"error": "Failed to join group"}), 400
        
    except Exception as e:
        print(f"Error in join_group: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/groups/<group_id>/members/<user_id>', methods=['DELETE'])
@require_db_connection
def leave_group(group_id, user_id):
    """Leave a group"""
    try:
        # Validate that group_id and user_id are not undefined or invalid
        if not group_id or group_id == 'undefined':
            return jsonify({"error": "Invalid group_id provided"}), 400
        
        if not user_id or user_id == 'undefined':
            return jsonify({"error": "Invalid user_id provided"}), 400
        
        # Validate ObjectId format
        try:
            ObjectId(group_id)
        except Exception:
            return jsonify({"error": "Invalid group_id format"}), 400
        
        try:
            ObjectId(user_id)
        except Exception:
            return jsonify({"error": "Invalid user_id format"}), 400
        
        success = group_service.remove_member(group_id, user_id)
        if success:
            # Notify group members
            emit_to_group_members(group_id, 'user_left', {
                'group_id': group_id,
                'user_id': user_id
            })
            return jsonify({"message": "Left group"}), 200
        return jsonify({"error": "Failed to leave group"}), 400
        
    except Exception as e:
        print(f"Error in leave_group: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/users/<user_id>/groups', methods=['GET'])
@require_db_connection
def get_user_groups(user_id):
    """Get user's groups"""
    groups = group_service.get_user_groups(user_id)
    return jsonify(groups), 200

@app.route('/api/groups/public', methods=['GET'])
@require_db_connection
def get_public_groups():
    """Get public groups"""
    limit = int(request.args.get('limit', 20))
    groups = group_service.get_public_groups(limit)
    return jsonify(groups), 200

@app.route('/api/groups/search', methods=['GET'])
@require_db_connection
def search_groups():
    """Search groups by name"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    groups = group_service.search_groups(query, limit)
    return jsonify(groups), 200

# =============================================================================
# MESSAGE ENDPOINTS
# =============================================================================

@app.route('/api/groups/<group_id>/messages', methods=['POST'])
@require_db_connection
def send_message(group_id):
    """Send a message to a group"""
    try:
        # Validate that group_id is not undefined or invalid
        if not group_id or group_id == 'undefined':
            return jsonify({"error": "Invalid group_id provided"}), 400
        
        # Validate ObjectId format
        try:
            ObjectId(group_id)
        except Exception:
            return jsonify({"error": "Invalid group_id format"}), 400
        
        data = request.get_json()
        sender_id = data.get('sender_id')
        content = data.get('content')
        message_type = data.get('type', 'text')
        reply_to = data.get('reply_to')
        
        if not sender_id or not content:
            return jsonify({"error": "sender_id and content required"}), 400
        
        # Check if user is a member of the group
        if not group_service.is_member(group_id, sender_id):
            return jsonify({"error": "User is not a member of this group"}), 403
        
        if reply_to:
            message = message_service.create_reply(sender_id, group_id, content, reply_to, message_type)
        else:
            message = message_service.create_message(sender_id, group_id, content, message_type)
        
        # Update group's last activity
        group_service.update_last_activity(group_id)
        
        # Emit real-time message to group members
        emit_to_group_members(group_id, 'new_message', message)
        
        return jsonify({"message": "Message sent", "data": message}), 201
        
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/groups/<group_id>/messages', methods=['GET'])
@require_db_connection
def get_messages(group_id):
    """Get messages for a group"""
    try:
        # Validate that group_id is not undefined or invalid
        if not group_id or group_id == 'undefined':
            return jsonify({"error": "Invalid group_id provided"}), 400
        
        # Validate ObjectId format
        try:
            ObjectId(group_id)
        except Exception:
            return jsonify({"error": "Invalid group_id format"}), 400
        
        # For now, we'll skip membership validation for get_messages to maintain compatibility
        # In a production system, you might want to add this validation:
        # user_id = request.args.get('user_id')
        # if user_id and not group_service.is_member(group_id, user_id):
        #     return jsonify({"error": "Access denied"}), 403
        
        limit = int(request.args.get('limit', 50))
        before = request.args.get('before')
        
        before_date = None
        if before:
            try:
                before_date = datetime.datetime.fromisoformat(before.replace('Z', '+00:00'))
            except:
                pass
        
        messages = message_service.get_group_messages(group_id, limit, before_date)
        return jsonify(messages), 200
        
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/messages/<message_id>', methods=['PUT'])
@require_db_connection
def edit_message(message_id):
    """Edit a message"""
    try:
        data = request.get_json()
        new_content = data.get('content')
        user_id = data.get('user_id')
        
        if not new_content or not user_id:
            return jsonify({"error": "content and user_id required"}), 400
        
        success = message_service.edit_message(message_id, new_content, user_id)
        if success:
            message = message_service.get_message(message_id)
            # Emit message update to group members
            emit_to_group_members(message['group_id'], 'message_edited', message)
            return jsonify({"message": "Message updated", "data": message}), 200
        return jsonify({"error": "Edit failed or insufficient permissions"}), 400
        
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/messages/<message_id>', methods=['DELETE'])
@require_db_connection
def delete_message(message_id):
    """Delete a message"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        message = message_service.get_message(message_id)
        if not message:
            return jsonify({"error": "Message not found"}), 404
        
        success = message_service.delete_message(message_id, user_id)
        if success:
            # Emit message deletion to group members
            emit_to_group_members(message['group_id'], 'message_deleted', {
                'message_id': message_id,
                'group_id': message['group_id']
            })
            return jsonify({"message": "Message deleted"}), 200
        return jsonify({"error": "Delete failed or insufficient permissions"}), 400
        
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/groups/<group_id>/messages/mark-read', methods=['POST'])
@require_db_connection
def mark_messages_read(group_id):
    """Mark messages as read"""
    try:
        # Validate that group_id is not undefined or invalid
        if not group_id or group_id == 'undefined':
            return jsonify({"error": "Invalid group_id provided"}), 400
        
        # Validate ObjectId format
        try:
            ObjectId(group_id)
        except Exception:
            return jsonify({"error": "Invalid group_id format"}), 400
        
        data = request.get_json()
        user_id = data.get('user_id')
        up_to = data.get('up_to')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        # Check if user is a member of the group
        if not group_service.is_member(group_id, user_id):
            return jsonify({"error": "User is not a member of this group"}), 403
        
        up_to_date = None
        if up_to:
            try:
                up_to_date = datetime.datetime.fromisoformat(up_to.replace('Z', '+00:00'))
            except:
                pass
        
        count = message_service.mark_group_messages_as_read(group_id, user_id, up_to_date)
        return jsonify({"message": f"Marked {count} messages as read"}), 200
        
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/users/<user_id>/unread', methods=['GET'])
@require_db_connection
def get_unread_counts(user_id):
    """Get unread message counts for all groups"""
    counts = message_service.get_unread_messages(user_id)
    return jsonify(counts), 200

# =============================================================================
# LOGGING ENDPOINTS
# =============================================================================

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get logs from the database with pagination support"""
    if not log_service:
        return jsonify({"error": "Database connection not available"}), 503
        
    try:
        # Parse query parameters
        limit = int(request.args.get('limit', 100))
        level = request.args.get('level')
        before = request.args.get('before')
        skip = int(request.args.get('skip', 0))
        page = request.args.get('page')
        
        # If page is provided, calculate skip from page number
        if page:
            page_num = int(page)
            if page_num > 0:
                skip = (page_num - 1) * limit
        
        before_date = None
        if before:
            try:
                before_date = datetime.datetime.fromisoformat(before.replace('Z', '+00:00'))
            except:
                return jsonify({"error": "Invalid 'before' date format"}), 400
        
        # Get logs with pagination
        result = log_service.get_logs(limit, level, before_date, skip)
        
        # Add pagination metadata
        result['pagination']['page'] = (skip // limit) + 1 if limit > 0 else 1
        result['pagination']['total_pages'] = (result['pagination']['total'] + limit - 1) // limit if limit > 0 else 1
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": "Failed to retrieve logs"}), 500

@app.route('/api/logs/simple', methods=['GET'])
def get_logs_simple():
    """Get logs from the database (simple format for backward compatibility)"""
    if not log_service:
        return jsonify({"error": "Database connection not available"}), 503
        
    try:
        limit = int(request.args.get('limit', 100))
        level = request.args.get('level')
        before = request.args.get('before')
        
        before_date = None
        if before:
            try:
                before_date = datetime.datetime.fromisoformat(before.replace('Z', '+00:00'))
            except:
                return jsonify({"error": "Invalid 'before' date format"}), 400
                
        logs = log_service.get_logs_simple(limit, level, before_date)
        return jsonify(logs), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve logs"}), 500

# =============================================================================
# WEBSOCKET EVENTS
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if log_service:
        try:
            log_service.create_log(
                message=f"Client connected: {request.sid}",
                url=request.url,
                level="INFO",
                extra_data={"sid": request.sid, "ip": request.remote_addr}
            )
        except Exception as e:
            print(f"Failed to log connection: {e}")
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user_id = connected_users.get(request.sid)
    if log_service:
        try:
            log_service.create_log(
                message=f"Client disconnected: {request.sid}",
                url=request.url,
                level="INFO",
                extra_data={"sid": request.sid, "user_id": user_id}
            )
        except Exception as e:
            print(f"Failed to log disconnection: {e}")
    print(f"Client disconnected: {request.sid}")
    
    # Remove user from connected users
    if request.sid in connected_users:
        user_id = connected_users[request.sid]
        
        # Remove socket from user's socket set
        if user_id in user_sockets:
            user_sockets[user_id].discard(request.sid)
            
            # If user has no more sockets, set them offline
            if not user_sockets[user_id] and user_service:
                try:
                    user_service.update_status(user_id, "offline")
                    del user_sockets[user_id]
                    
                    # Notify friends that user went offline
                    friends = user_service.get_friends(user_id)
                    for friend in friends:
                        emit_to_user(friend['id'], 'user_status_changed', {
                            'user_id': user_id,
                            'status': 'offline'
                        })
                except Exception as e:
                    print(f"Failed to update user status on disconnect: {e}")
        
        del connected_users[request.sid]

@socketio.on('user_online')
def handle_user_online(data):
    """Handle user coming online"""
    user_id = data.get('user_id')
    if not user_id:
        if log_service:
            try:
                log_service.create_log("user_online event without user_id", request.url, "WARNING", data)
            except:
                pass
        return
    
    if not user_service:
        emit('error', {'message': 'Database connection not available'})
        return
    
    if log_service:
        try:
            log_service.create_log(f"User {user_id} came online", request.url, "INFO", {"user_id": user_id, "sid": request.sid})
        except Exception as e:
            print(f"Failed to log user online: {e}")
    
    # Track the connection
    connected_users[request.sid] = user_id
    
    if user_id not in user_sockets:
        user_sockets[user_id] = set()
    user_sockets[user_id].add(request.sid)
    
    try:
        # Update user status to online
        user_service.update_status(user_id, "online")
        
        # Notify friends that user is online
        friends = user_service.get_friends(user_id)
        for friend in friends:
            emit_to_user(friend['id'], 'user_status_changed', {
                'user_id': user_id,
                'status': 'online'
            })
        
        # Join user to their group rooms
        if group_service:
            groups = group_service.get_user_groups(user_id)
            for group in groups:
                join_room(f"group_{group['id']}")
    except Exception as e:
        print(f"Error handling user online: {e}")
        emit('error', {'message': 'Failed to set user online'})

@socketio.on('join_group')
def handle_join_group(data):
    """Handle user joining a group room"""
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    
    if group_id and user_id and group_service:
        try:
            if group_service.is_member(group_id, user_id):
                join_room(f"group_{group_id}")
                emit('joined_group', {'group_id': group_id})
        except Exception as e:
            print(f"Error joining group: {e}")
            emit('error', {'message': 'Failed to join group'})

@socketio.on('leave_group')
def handle_leave_group(data):
    """Handle user leaving a group room"""
    group_id = data.get('group_id')
    if group_id:
        leave_room(f"group_{group_id}")
        emit('left_group', {'group_id': group_id})

@socketio.on('typing_start')
def handle_typing_start(data):
    """Handle user starting to type"""
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    
    if group_id and user_id and group_service and user_service:
        try:
            if group_service.is_member(group_id, user_id):
                if log_service:
                    try:
                        log_service.create_log(f"User {user_id} started typing in group {group_id}", request.url, "DEBUG", data)
                    except:
                        pass
                
                # Update typing status in services
                group_service.set_user_typing(group_id, user_id, True)
                user_service.set_typing_status(user_id, group_id, True)
                
                # Notify other group members
                emit_to_group_members(group_id, 'user_typing', {
                    'group_id': group_id,
                    'user_id': user_id,
                    'is_typing': True
                }, exclude_user=user_id)
        except Exception as e:
            print(f"Error handling typing start: {e}")

@socketio.on('typing_stop')
def handle_typing_stop(data):
    """Handle user stopping typing"""
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    
    if group_id and user_id and group_service and user_service:
        try:
            if log_service:
                try:
                    log_service.create_log(f"User {user_id} stopped typing in group {group_id}", request.url, "DEBUG", data)
                except:
                    pass
            
            # Update typing status in services
            group_service.set_user_typing(group_id, user_id, False)
            user_service.set_typing_status(user_id, group_id, False)
            
            # Notify other group members
            emit_to_group_members(group_id, 'user_typing', {
                'group_id': group_id,
                'user_id': user_id,
                'is_typing': False
            }, exclude_user=user_id)
        except Exception as e:
            print(f"Error handling typing stop: {e}")

@socketio.on('ping')
def handle_ping():
    """Handle ping for keepalive"""
    emit('pong')

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
