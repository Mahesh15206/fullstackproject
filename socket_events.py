# socket_events.py — SocketIO real-time event handlers

from flask import session
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
from db import get_db


def register_socket_events(socketio):
    """Register all SocketIO event handlers."""

    @socketio.on('join')
    def on_join(data):
        """User joins a chat room for real-time messages."""
        room = str(data['room'])
        join_room(room)

    @socketio.on('leave')
    def on_leave(data):
        """User leaves a chat room."""
        room = str(data['room'])
        leave_room(room)

    @socketio.on('send_message')
    def handle_message(data):
        """Receive and broadcast a new chat message in real-time."""
        room_id = str(data.get('room'))
        message_text = data.get('message', '')
        message_type = data.get('message_type', 'text')
        file_path = data.get('file_path')
        msg_id = data.get('msg_id')

        user_id = session.get('user_id')
        user_name = session.get('user_name')

        if not user_id:
            return

        is_valid_voice = (message_type == 'voice' and file_path)
        is_valid_text = (message_type == 'text' and message_text.strip())

        if is_valid_text or is_valid_voice:
            if is_valid_text:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO messages (room_id, sender_id, message_text) VALUES (%s, %s, %s)",
                    (room_id, user_id, message_text)
                )
                msg_id = cursor.lastrowid
                conn.commit()
                cursor.close()
                conn.close()

            emit('receive_message', {
                'msg_id': msg_id,
                'sender_name': user_name,
                'sender_id': user_id,
                'message': message_text,
                'message_type': message_type,
                'file_path': file_path,
                'sent_at': datetime.now().strftime('%H:%M')
            }, room=room_id)
