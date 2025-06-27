# Chat App Backend - Improved Architecture

A modern, real-time chat application backend built with Flask, Socket.IO, and MongoDB. This backend provides a comprehensive API for user management, group chats, messaging, and real-time features.

## Features

### Core Functionality
- **User Management**: Registration, authentication, profiles, friends system
- **Group Chat**: Create/join groups, member management, admin controls
- **Real-time Messaging**: Instant message delivery, typing indicators, online status
- **Message Features**: Edit/delete messages, replies, read receipts, search
- **Security**: Password hashing, input validation, permission controls

### Real-time Features
- **Online Status**: See who's online in real-time
- **Typing Indicators**: See when users are typing in groups
- **Live Messaging**: Instant message delivery via WebSocket
- **Connection Management**: Automatic online/offline status updates

## Project Structure

```
├── services/
│   ├── base_repository.py      # MongoDB repository base class
│   ├── user_service.py         # User management service
│   ├── group_service.py        # Group/chat room service
│   └── message_service.py      # Message handling service
├── db_methods_user_data_service/  # Legacy data models (kept for compatibility)
├── server.py                   # Main Flask-SocketIO application
├── settings.py                 # Database configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## API Endpoints

### User Management
- `POST /api/users/register` - Register new user
- `POST /api/users/login` - Login user
- `GET /api/users/<user_id>` - Get user details
- `PUT /api/users/<user_id>` - Update user profile
- `GET /api/users/<user_id>/friends` - Get friends list
- `POST /api/users/<user_id>/friends/<friend_id>` - Add friend
- `DELETE /api/users/<user_id>/friends/<friend_id>` - Remove friend
- `GET /api/users/search?q=<query>` - Search users
- `GET /api/users/online` - Get online users

### Group Management
- `POST /api/groups` - Create group
- `GET /api/groups/<group_id>` - Get group details
- `PUT /api/groups/<group_id>` - Update group (admin only)
- `POST /api/groups/<group_id>/members/<user_id>` - Join group
- `DELETE /api/groups/<group_id>/members/<user_id>` - Leave group
- `GET /api/users/<user_id>/groups` - Get user's groups
- `GET /api/groups/public` - Get public groups
- `GET /api/groups/search?q=<query>` - Search groups

### Messaging
- `POST /api/groups/<group_id>/messages` - Send message
- `GET /api/groups/<group_id>/messages` - Get messages (with pagination)
- `PUT /api/messages/<message_id>` - Edit message
- `DELETE /api/messages/<message_id>` - Delete message
- `POST /api/groups/<group_id>/messages/mark-read` - Mark messages as read
- `GET /api/users/<user_id>/unread` - Get unread message counts

## WebSocket Events

### Client → Server
- `user_online` - User comes online
- `join_group` - Join group room
- `leave_group` - Leave group room
- `typing_start` - Start typing in group
- `typing_stop` - Stop typing in group
- `ping` - Keepalive ping

### Server → Client
- `new_message` - New message received
- `message_edited` - Message was edited
- `message_deleted` - Message was deleted
- `user_joined` - User joined group
- `user_left` - User left group
- `user_typing` - User typing status changed
- `user_status_changed` - User online/offline status changed
- `pong` - Keepalive response

## Database Schema

### Users Collection
```json
{
  "_id": "ObjectId",
  "username": "string",
  "password": "hashed_string",
  "profile_pic": "string",
  "status": "online|offline",
  "friends": ["user_id"],
  "last_active": "datetime",
  "is_typing_in": ["group_id"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Groups Collection
```json
{
  "_id": "ObjectId",
  "name": "string",
  "description": "string",
  "creator_id": "string",
  "is_private": "boolean",
  "members": ["user_id"],
  "admins": ["user_id"],
  "typing_users": ["user_id"],
  "last_activity": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Messages Collection
```json
{
  "_id": "ObjectId",
  "sender_id": "string",
  "group_id": "string",
  "content": "string",
  "type": "text|image|file",
  "read_by": ["user_id"],
  "edited": "boolean",
  "reply_to": "message_id|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Database**
   Update `settings.py` with your MongoDB connection string:
   ```python
   DB_CONNECTION_STRING = "mongodb://localhost:27017/"
   DB_NAME = "chat_app"
   ```

3. **Run the Server**
   ```bash
   python server.py
   ```

4. **Access the API**
   - REST API: `http://localhost:5000/api/`
   - WebSocket: `ws://localhost:5000/socket.io/`

## Usage Examples

### Register a User
```bash
curl -X POST http://localhost:5000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'
```

### Create a Group
```bash
curl -X POST http://localhost:5000/api/groups \
  -H "Content-Type: application/json" \
  -d '{"name": "General Chat", "creator_id": "user_id", "description": "Main chat room"}'
```

### Send a Message
```bash
curl -X POST http://localhost:5000/api/groups/group_id/messages \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "user_id", "content": "Hello everyone!"}'
```

## Key Improvements

1. **Simplified Architecture**: Clean service layer with repository pattern
2. **Real-time Features**: WebSocket support for live updates
3. **Better Security**: Password hashing, input validation
4. **Scalable Design**: Stateless backend, efficient database queries
5. **Modern API**: RESTful endpoints with proper HTTP status codes
6. **Rich Features**: Typing indicators, read receipts, message replies
7. **Easy to Extend**: Modular service architecture

## Development Notes

- The backend is completely stateless except for WebSocket connection tracking
- All real-time features use WebSocket events for instant updates
- Database operations are optimized with proper indexing and aggregation
- Error handling is implemented throughout the API
- The service layer abstracts database operations for easy testing

## Future Enhancements

- File upload support for images and documents
- Push notifications for offline users
- Message encryption for private chats
- Rate limiting and spam protection
- User roles and permissions system
- Message search with full-text indexing 