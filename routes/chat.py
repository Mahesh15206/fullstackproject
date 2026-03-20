# routes/chat.py — Chat, Voice Messages, and Delete Message routes

import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from db import get_db
from helpers import login_required

chat_bp = Blueprint('chat_bp', __name__)


@chat_bp.route('/my_chats')
@login_required
def my_chats():
    """Show all chat rooms with unread message count."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    user_id = session['user_id']

    cursor.execute("""
        SELECT chat_rooms.*,
            CASE WHEN chat_rooms.user1_id = %s THEN u2.name ELSE u1.name END AS partner_name,
            CASE WHEN chat_rooms.user1_id = %s THEN u2.profile_pic ELSE u1.profile_pic END AS partner_pic,
            CASE WHEN chat_rooms.user1_id = %s THEN u2.id ELSE u1.id END AS partner_id,
            (SELECT COUNT(*) FROM messages WHERE messages.room_id = chat_rooms.id
             AND messages.sender_id != %s AND messages.is_read = FALSE) AS unread_count
        FROM chat_rooms
        JOIN users u1 ON chat_rooms.user1_id = u1.id
        JOIN users u2 ON chat_rooms.user2_id = u2.id
        WHERE chat_rooms.user1_id = %s OR chat_rooms.user2_id = %s
        ORDER BY chat_rooms.created_at DESC
    """, (user_id, user_id, user_id, user_id, user_id, user_id))
    chats = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('my_chats.html', chats=chats)


@chat_bp.route('/chat/<int:room_id>')
@login_required
def chat(room_id):
    """Open a chat room and load messages."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM chat_rooms
        WHERE id = %s AND (user1_id = %s OR user2_id = %s)
    """, (room_id, session['user_id'], session['user_id']))
    room = cursor.fetchone()

    if not room:
        flash('Chat room not found.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('chat_bp.my_chats'))

    cursor.execute("""
        UPDATE messages SET is_read = TRUE
        WHERE room_id = %s AND sender_id != %s
    """, (room_id, session['user_id']))
    conn.commit()

    cursor.execute("""
        SELECT messages.*, users.name AS sender_name
        FROM messages
        JOIN users ON messages.sender_id = users.id
        WHERE messages.room_id = %s
        ORDER BY messages.sent_at ASC
    """, (room_id,))
    messages_list = cursor.fetchall()

    partner_id = room['user2_id'] if room['user1_id'] == session['user_id'] else room['user1_id']
    cursor.execute("SELECT name, profile_pic FROM users WHERE id = %s", (partner_id,))
    partner = cursor.fetchone()

    cursor.close()
    conn.close()
    return render_template('chat.html', room=room, messages=messages_list,
                           partner=partner, room_id=room_id)


@chat_bp.route('/upload_voice/<int:room_id>', methods=['POST'])
@login_required
def upload_voice(room_id):
    """Handle voice message upload via AJAX."""
    if 'voice' not in request.files:
        return jsonify({'error': 'No voice file'}), 400

    file = request.files['voice']
    if file:
        filename = secure_filename(f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.webm")
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'voice_msgs')
        os.makedirs(upload_path, exist_ok=True)
        file.save(os.path.join(upload_path, filename))

        conn = get_db()
        cursor = conn.cursor()
        file_path = f"uploads/voice_msgs/{filename}"
        cursor.execute(
            "INSERT INTO messages (room_id, sender_id, message_type, file_path) VALUES (%s, %s, 'voice', %s)",
            (room_id, session['user_id'], file_path)
        )
        msg_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'file_path': file_path, 'msg_id': msg_id})

    return jsonify({'error': 'Upload failed'}), 400


@chat_bp.route('/delete_message/<int:msg_id>', methods=['POST'])
@login_required
def delete_message(msg_id):
    """Delete a chat message."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT sender_id FROM messages WHERE id = %s", (msg_id,))
    msg = cursor.fetchone()

    if msg and msg['sender_id'] == session['user_id']:
        cursor.execute("DELETE FROM messages WHERE id = %s", (msg_id,))
        conn.commit()
        success = True
    else:
        success = False

    cursor.close()
    conn.close()
    return jsonify({'success': success})
