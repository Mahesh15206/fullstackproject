# routes/dashboard.py — Dashboard, View Profile, and Endorse routes

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db
from helpers import login_required

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Show matching users based on complementary skills with a match percentage."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    user_id = session['user_id']
    search_query = request.args.get('q', '').strip().lower()

    cursor.execute("""
        SELECT blocked_id FROM blocked_users WHERE blocker_id = %s
        UNION
        SELECT blocker_id FROM blocked_users WHERE blocked_id = %s
    """, (user_id, user_id))
    blocked_ids = {row['blocked_id'] if 'blocked_id' in row else row['blocker_id'] for row in cursor.fetchall()}

    # Fetch all users (except current) with their offered skills for the browse section
    cursor.execute("""
        SELECT users.id, users.name, users.profile_pic, users.location,
               GROUP_CONCAT(skills_offered.skill_name SEPARATOR ', ') AS skills
        FROM users
        LEFT JOIN skills_offered ON users.id = skills_offered.user_id
        WHERE users.id != %s
        GROUP BY users.id
        ORDER BY users.name ASC
    """, (user_id,))
    
    all_users_with_skills = []
    for u in cursor.fetchall():
        if u['id'] in blocked_ids:
            continue
        if search_query:
            search_match = False
            if search_query in u['name'].lower():
                search_match = True
            elif u['skills'] and search_query in u['skills'].lower():
                search_match = True
            if not search_match:
                continue
        all_users_with_skills.append(u)

    cursor.close()
    conn.close()
    return render_template('dashboard.html', 
                           search_query=request.args.get('q', ''),
                           all_users_with_skills=all_users_with_skills)


@dashboard_bp.route('/user/<int:user_id>')
@login_required
def view_profile(user_id):
    """View another user's public profile."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        flash('User not found.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard_bp.dashboard'))

    cursor.execute("SELECT * FROM skills_offered WHERE user_id = %s", (user_id,))
    skills_offered = cursor.fetchall()

    cursor.execute("SELECT * FROM skills_wanted WHERE user_id = %s", (user_id,))
    skills_wanted = cursor.fetchall()

    cursor.execute("""
        SELECT endorsements.skill_name, users.name AS endorser_name
        FROM endorsements
        JOIN users ON endorsements.endorser_id = users.id
        WHERE endorsements.endorsed_id = %s
    """, (user_id,))
    endorsements = cursor.fetchall()

    cursor.execute("""
        SELECT reviews.*, users.name AS reviewer_name
        FROM reviews
        JOIN users ON reviews.reviewer_id = users.id
        WHERE reviews.reviewed_id = %s
        ORDER BY reviews.created_at DESC
    """, (user_id,))
    reviews = cursor.fetchall()

    cursor.execute("""
        SELECT skill_name FROM endorsements
        WHERE endorser_id = %s AND endorsed_id = %s
    """, (session['user_id'], user_id))
    already_endorsed = {row['skill_name'] for row in cursor.fetchall()}

    cursor.close()
    conn.close()
    return render_template('view_profile.html', user=user, skills_offered=skills_offered,
                           skills_wanted=skills_wanted, endorsements=endorsements,
                           reviews=reviews, already_endorsed=already_endorsed)


@dashboard_bp.route('/endorse/<int:user_id>/<skill_name>')
@login_required
def endorse(user_id, skill_name):
    """Endorse another user's skill."""
    if user_id == session['user_id']:
        flash('You cannot endorse yourself.', 'warning')
        return redirect(url_for('dashboard_bp.view_profile', user_id=user_id))

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO endorsements (endorser_id, endorsed_id, skill_name) VALUES (%s, %s, %s)",
            (session['user_id'], user_id, skill_name)
        )
        conn.commit()
        flash(f'You endorsed {skill_name}!', 'success')
    except:
        flash('Already endorsed this skill.', 'info')
    cursor.close()
    conn.close()
    return redirect(url_for('dashboard_bp.view_profile', user_id=user_id))
