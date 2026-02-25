# routes/user/notifications.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.notification import Notification # Import the Notification model
from routes.user import user_bp

# Define the user notifications blueprint
# Make sure this matches the import in routes/user/__init__.py
# The url_prefix='/user' is defined in routes/user/__init__.py
user_notifications_bp = Blueprint('user_notifications', __name__)

@user_bp.route('/notifications')
@login_required
def list_notifications():
    """List the current user's notifications."""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    notifications_query = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.timestamp.desc())

    notifications_pagination = notifications_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    notifications = notifications_pagination.items

    context = {
        'user': current_user,
        'notifications': notifications,
        'notifications_pagination': notifications_pagination
    }

    return render_template('user/notifications/list.html', **context)

# --- CRITICAL FIX: Ensure this route exists ---
@user_bp.route('/notifications/<int:notification_id>/mark_as_read', methods=['POST'])
@login_required
def mark_notification_as_read(notification_id):
    """Mark a specific notification as read."""
    notification = Notification.query.get_or_404(notification_id)

    # Authorization check
    if notification.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('car.home'))

    notification.mark_as_read()
    db.session.commit()

    flash('Notification marked as read.', 'success')
    # Redirect back, preserving page number if needed
    page = request.args.get('page', 1, type=int)
    return redirect(url_for('user.list_notifications', page=page))
# --- END CRITICAL FIX ---

@user_bp.route('/notifications/mark_all_as_read', methods=['POST'])
@login_required
def mark_all_notifications_as_read():
    """Mark all notifications for the current user as read."""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({Notification.is_read: True})

    db.session.commit()

    flash('All notifications marked as read.', 'success')
    return redirect(url_for('user.list_notifications'))

# --- CRITICAL FIX: Define the route for marking all notifications as read ---