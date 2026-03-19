# routes/admin.py — Admin Panel routes

from flask import Blueprint, render_template, redirect, url_for, flash
from db import get_db
from helpers import admin_required

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_required
def admin_dashboard():
    """Admin dashboard with counts and overview."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS count FROM users")
    user_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) AS count FROM swap_requests WHERE status = 'pending'")
    pending_requests = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) AS count FROM reports WHERE status = 'pending'")
    pending_reports = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) AS count FROM sessions WHERE status = 'completed'")
    completed_sessions = cursor.fetchone()['count']

    cursor.close()
    conn.close()
    return render_template('admin/dashboard.html',
                           user_count=user_count, pending_requests=pending_requests,
                           pending_reports=pending_reports, completed_sessions=completed_sessions)


@admin_bp.route('/users')
@admin_required
def admin_users():
    """Admin: list all users."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/delete_user/<int:user_id>')
@admin_required
def admin_delete_user(user_id):
    """Admin: delete a user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('User deleted.', 'info')
    return redirect(url_for('admin_bp.admin_users'))


@admin_bp.route('/reports')
@admin_required
def admin_reports():
    """Admin: view and manage reports."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT reports.*, u1.name AS reporter_name, u2.name AS reported_name
        FROM reports
        JOIN users u1 ON reports.reporter_id = u1.id
        JOIN users u2 ON reports.reported_id = u2.id
        ORDER BY reports.status ASC, reports.id DESC
    """)
    reports = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/reports.html', reports=reports)


@admin_bp.route('/resolve_report/<int:report_id>')
@admin_required
def resolve_report(report_id):
    """Admin: mark a report as resolved."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE reports SET status = 'resolved' WHERE id = %s", (report_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Report resolved.', 'success')
    return redirect(url_for('admin_bp.admin_reports'))
