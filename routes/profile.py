# routes/profile.py — Profile, Skills, and Quiz routes

import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from db import get_db
from helpers import login_required, allowed_file, ALLOWED_IMAGE_EXTENSIONS

profile_bp = Blueprint('profile_bp', __name__)


@profile_bp.route('/profile')
@login_required
def profile():
    """Show the logged-in user's own profile with their skills."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM skills_offered WHERE user_id = %s", (session['user_id'],))
    skills_offered = cursor.fetchall()

    cursor.execute("SELECT * FROM skills_wanted WHERE user_id = %s", (session['user_id'],))
    skills_wanted = cursor.fetchall()

    cursor.execute("""
        SELECT endorsements.skill_name, users.name AS endorser_name
        FROM endorsements
        JOIN users ON endorsements.endorser_id = users.id
        WHERE endorsements.endorsed_id = %s
    """, (session['user_id'],))
    endorsements = cursor.fetchall()

    cursor.execute("""
        SELECT reviews.*, users.name AS reviewer_name
        FROM reviews
        JOIN users ON reviews.reviewer_id = users.id
        WHERE reviews.reviewed_id = %s
        ORDER BY reviews.created_at DESC
    """, (session['user_id'],))
    reviews = cursor.fetchall()

    # Get all unique skills offered by OTHER users (for the "Browse Available Skills" section)
    cursor.execute("""
        SELECT skills_offered.skill_name, users.name AS offered_by, users.id AS user_id
        FROM skills_offered
        JOIN users ON skills_offered.user_id = users.id
        WHERE skills_offered.user_id != %s
        ORDER BY skills_offered.skill_name ASC
    """, (session['user_id'],))
    available_skills = cursor.fetchall()

    # Get current user's wanted skill names (lowercase) to mark already-added ones
    my_wanted_names = {s['skill_name'].lower() for s in skills_wanted}

    cursor.close()
    conn.close()
    return render_template('profile.html', user=user, skills_offered=skills_offered,
                           skills_wanted=skills_wanted, endorsements=endorsements,
                           reviews=reviews, available_skills=available_skills,
                           my_wanted_names=my_wanted_names)


@profile_bp.route('/add_skill/<skill_type>', methods=['POST'])
@login_required
def add_skill(skill_type):
    """Add a skill the user can teach or wants to learn."""
    if skill_type not in ['offered', 'wanted']:
        return redirect(url_for('profile_bp.profile'))

    skill_name = request.form['skill_name']
    category = request.form.get('category', '')
    table = f"skills_{skill_type}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO {table} (user_id, skill_name, category) VALUES (%s, %s, %s)",
        (session['user_id'], skill_name, category)
    )
    conn.commit()
    cursor.close()
    conn.close()

    msg = 'Skill added!' if skill_type == 'offered' else 'Skill added to your want-to-learn list!'
    flash(msg, 'success')
    return redirect(url_for('profile_bp.profile'))


@profile_bp.route('/remove_skill/<skill_type>/<int:skill_id>')
@login_required
def remove_skill(skill_type, skill_id):
    """Remove a skill the user offered or wanted."""
    if skill_type not in ['offered', 'wanted']:
        return redirect(url_for('profile_bp.profile'))

    table = f"skills_{skill_type}"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id = %s AND user_id = %s",
                   (skill_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Skill removed.', 'info')
    return redirect(url_for('profile_bp.profile'))


@profile_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile details and optionally change password."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        location = request.form.get('location', '')
        bio = request.form.get('bio', '')
        new_password = request.form.get('new_password', '')

        profile_pic_filename = None
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '' and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                profile_pic_filename = secure_filename(f"{session['user_id']}_{file.filename}")
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_pics')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, profile_pic_filename))

        if not profile_pic_filename:
            emoji_avatar = request.form.get('emoji_avatar')
            if emoji_avatar in ['emoji_boy.svg', 'emoji_girl.svg']:
                profile_pic_filename = emoji_avatar

        if new_password:
            hashed = generate_password_hash(new_password)
            if profile_pic_filename:
                cursor.execute(
                    "UPDATE users SET name=%s, location=%s, bio=%s, password=%s, profile_pic=%s WHERE id=%s",
                    (name, location, bio, hashed, profile_pic_filename, session['user_id'])
                )
            else:
                cursor.execute(
                    "UPDATE users SET name=%s, location=%s, bio=%s, password=%s WHERE id=%s",
                    (name, location, bio, hashed, session['user_id'])
                )
        else:
            if profile_pic_filename:
                cursor.execute(
                    "UPDATE users SET name=%s, location=%s, bio=%s, profile_pic=%s WHERE id=%s",
                    (name, location, bio, profile_pic_filename, session['user_id'])
                )
            else:
                cursor.execute(
                    "UPDATE users SET name=%s, location=%s, bio=%s WHERE id=%s",
                    (name, location, bio, session['user_id'])
                )
        conn.commit()
        session['user_name'] = name
        flash('Profile updated!', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('profile_bp.profile'))

    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_profile.html', user=user)


@profile_bp.route('/quiz/<skill_name>')
@login_required
def quiz(skill_name):
    """Show quiz questions for a specific skill."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM quiz_questions WHERE skill_name = %s", (skill_name,))
    questions = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('quiz.html', skill_name=skill_name, questions=questions)


@profile_bp.route('/submit_quiz/<skill_name>', methods=['POST'])
@login_required
def submit_quiz(skill_name):
    """Grade the quiz and mark the skill as verified if the user passes."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM quiz_questions WHERE skill_name = %s", (skill_name,))
    questions = cursor.fetchall()

    correct = 0
    total = len(questions)

    for q in questions:
        user_answer = request.form.get(f"answer_{q['id']}", '')
        if user_answer.upper() == q['correct_option']:
            correct += 1

    percentage = (correct / total * 100) if total > 0 else 0

    if percentage >= 70:
        cursor.execute(
            "UPDATE skills_offered SET is_verified = TRUE WHERE user_id = %s AND skill_name = %s",
            (session['user_id'], skill_name)
        )
        conn.commit()
        flash(f'Congratulations! You scored {correct}/{total} ({percentage:.0f}%). Skill verified!', 'success')
    else:
        flash(f'You scored {correct}/{total} ({percentage:.0f}%). Need 70% to pass. Try again!', 'warning')

    cursor.close()
    conn.close()
    return redirect(url_for('profile_bp.profile'))
