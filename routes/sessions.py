# routes/sessions.py — Sessions, Progress, and Review routes

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db
from helpers import login_required

sessions_bp = Blueprint('sessions_bp', __name__)


@sessions_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    """Book and view learning sessions."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    user_id = session['user_id']

    if request.method == 'POST':
        partner_id = request.form['partner_id']
        topic = request.form['topic']
        session_datetime = request.form['session_datetime']

        cursor.execute(
            "INSERT INTO sessions (organizer_id, partner_id, topic, session_datetime) VALUES (%s, %s, %s, %s)",
            (user_id, partner_id, topic, session_datetime)
        )
        conn.commit()
        flash('Session scheduled!', 'success')

    cursor.execute("""
        SELECT sessions.*,
            u1.name AS organizer_name,
            u2.name AS partner_name
        FROM sessions
        JOIN users u1 ON sessions.organizer_id = u1.id
        JOIN users u2 ON sessions.partner_id = u2.id
        WHERE sessions.organizer_id = %s OR sessions.partner_id = %s
        ORDER BY sessions.session_datetime DESC
    """, (user_id, user_id))
    sessions_list = cursor.fetchall()

    cursor.execute("""
        SELECT users.id, users.name
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
    return render_template('schedule.html', sessions=sessions_list, partners=partners)


@sessions_bp.route('/complete_session/<int:session_id>')
@login_required
def complete_session(session_id):
    """Mark a session as completed and update learning progress."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
    sess = cursor.fetchone()

    if sess:
        cursor.execute("UPDATE sessions SET status = 'completed' WHERE id = %s", (session_id,))

        for uid in [sess['organizer_id'], sess['partner_id']]:
            cursor.execute("""
                UPDATE learning_goals
                SET completed_sessions = completed_sessions + 1,
                    is_achieved = CASE WHEN completed_sessions + 1 >= target_sessions THEN TRUE ELSE FALSE END
                WHERE user_id = %s AND skill_name = %s
            """, (uid, sess['topic']))

        conn.commit()
        flash('Session marked as completed!', 'success')

    cursor.close()
    conn.close()
    return redirect(url_for('sessions_bp.schedule'))


@sessions_bp.route('/cancel_session/<int:session_id>')
@login_required
def cancel_session(session_id):
    """Cancel a scheduled session."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET status = 'cancelled' WHERE id = %s", (session_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Session cancelled.', 'info')
    return redirect(url_for('sessions_bp.schedule'))


@sessions_bp.route('/progress', methods=['GET', 'POST'])
@login_required
def progress():
    """Track learning goals with progress bars."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    user_id = session['user_id']

    if request.method == 'POST':
        skill_name = request.form['skill_name']
        target_sessions = request.form.get('target_sessions', 5)
        cursor.execute(
            "INSERT INTO learning_goals (user_id, skill_name, target_sessions) VALUES (%s, %s, %s)",
            (user_id, skill_name, target_sessions)
        )
        conn.commit()
        flash('Learning goal added!', 'success')

    cursor.execute("SELECT * FROM learning_goals WHERE user_id = %s", (user_id,))
    goals = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('progress.html', goals=goals)


@sessions_bp.route('/review/<int:user_id>', methods=['GET', 'POST'])
@login_required
def review(user_id):
    """Leave a star rating and comment for another user."""
    if user_id == session['user_id']:
        flash('You cannot review yourself.', 'warning')
        return redirect(url_for('dashboard_bp.dashboard'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        rating = request.form['rating']
        comment = request.form.get('comment', '')
        cursor.execute(
            "INSERT INTO reviews (reviewer_id, reviewed_id, rating, comment) VALUES (%s, %s, %s, %s)",
            (session['user_id'], user_id, rating, comment)
        )
        conn.commit()
        flash('Review submitted!', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard_bp.view_profile', user_id=user_id))

    cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
    reviewed_user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('review.html', reviewed_user=reviewed_user, user_id=user_id)
