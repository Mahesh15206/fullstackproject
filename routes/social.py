# routes/social.py — Swap Requests, Connections, Block, and Report routes

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db
from helpers import login_required

social_bp = Blueprint('social_bp', __name__)


@social_bp.route('/send_request/<int:receiver_id>')
@login_required
def send_request(receiver_id):
    """Send a skill swap request to another user."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM swap_requests
        WHERE ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s))
        AND status IN ('pending', 'accepted')
    """, (session['user_id'], receiver_id, receiver_id, session['user_id']))
    existing = cursor.fetchone()

    if existing:
        flash('A swap request already exists between you two.', 'info')
    else:
        cursor.execute(
            "INSERT INTO swap_requests (sender_id, receiver_id) VALUES (%s, %s)",
            (session['user_id'], receiver_id)
        )
        conn.commit()
        flash('Swap request sent!', 'success')

    cursor.close()
    conn.close()
    return redirect(url_for('dashboard_bp.dashboard'))


@social_bp.route('/requests')
@login_required
def requests_page():
    """Show all swap requests and accepted connections in one page."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    user_id = session['user_id']

    # Incoming pending requests
    cursor.execute("""
        SELECT swap_requests.*, users.name AS sender_name, users.profile_pic AS sender_pic
        FROM swap_requests
        JOIN users ON swap_requests.sender_id = users.id
        WHERE swap_requests.receiver_id = %s AND swap_requests.status = 'pending'
        ORDER BY swap_requests.created_at DESC
    """, (user_id,))
    incoming = cursor.fetchall()

    # Outgoing requests (all statuses)
    cursor.execute("""
        SELECT swap_requests.*, users.name AS receiver_name, users.profile_pic AS receiver_pic
        FROM swap_requests
        JOIN users ON swap_requests.receiver_id = users.id
        WHERE swap_requests.sender_id = %s
        ORDER BY swap_requests.created_at DESC
    """, (user_id,))
    outgoing = cursor.fetchall()

    # Accepted connections
    cursor.execute("""
        SELECT users.id, users.name, users.profile_pic, users.location
        FROM swap_requests
        JOIN users ON (
            CASE
                WHEN swap_requests.sender_id = %s THEN swap_requests.receiver_id
                ELSE swap_requests.sender_id
            END = users.id
        )
        WHERE (swap_requests.sender_id = %s OR swap_requests.receiver_id = %s)
        AND swap_requests.status = 'accepted'
    """, (user_id, user_id, user_id))
    partners = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('requests.html', incoming=incoming, outgoing=outgoing, partners=partners)


@social_bp.route('/accept_request/<int:request_id>')
@login_required
def accept_request(request_id):
    """Accept a swap request and create a chat room."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM swap_requests WHERE id = %s AND receiver_id = %s",
                   (request_id, session['user_id']))
    req = cursor.fetchone()

    if req:
        cursor.execute("UPDATE swap_requests SET status = 'accepted' WHERE id = %s", (request_id,))
        cursor.execute(
            "INSERT INTO chat_rooms (user1_id, user2_id) VALUES (%s, %s)",
            (req['sender_id'], req['receiver_id'])
        )
        conn.commit()
        flash('Request accepted! Chat room created.', 'success')
    else:
        flash('Request not found.', 'danger')

    cursor.close()
    conn.close()
    return redirect(url_for('social_bp.requests_page'))


@social_bp.route('/reject_request/<int:request_id>')
@login_required
def reject_request(request_id):
    """Reject a swap request."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE swap_requests SET status = 'rejected' WHERE id = %s AND receiver_id = %s",
                   (request_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Request rejected.', 'info')
    return redirect(url_for('social_bp.requests_page'))


@social_bp.route('/cancel_request/<int:request_id>')
@login_required
def cancel_request(request_id):
    """Cancel an outgoing swap request."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE swap_requests SET status = 'cancelled' WHERE id = %s AND sender_id = %s",
                   (request_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Request cancelled.', 'info')
    return redirect(url_for('social_bp.requests_page'))


@social_bp.route('/block/<int:user_id>')
@login_required
def block_user(user_id):
    """Block another user."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO blocked_users (blocker_id, blocked_id) VALUES (%s, %s)",
            (session['user_id'], user_id)
        )
        conn.commit()
        flash('User blocked.', 'info')
    except:
        flash('Already blocked.', 'info')
    cursor.close()
    conn.close()
    return redirect(url_for('dashboard_bp.dashboard'))


@social_bp.route('/report/<int:user_id>', methods=['POST'])
@login_required
def report_user(user_id):
    """Report a user for bad behavior."""
    reason = request.form['reason']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reports (reporter_id, reported_id, reason) VALUES (%s, %s, %s)",
        (session['user_id'], user_id, reason)
    )
    conn.commit()
    cursor.close()
    conn.close()
    flash('Report submitted. Admins will review it.', 'info')
    return redirect(url_for('dashboard_bp.view_profile', user_id=user_id))
