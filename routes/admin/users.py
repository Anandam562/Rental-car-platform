# routes/admin/user.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import admin_bp
from models import db
from models.user import User


@admin_bp.route('/users')
@login_required
def list_users():
    """
    List all users with search and pagination.
    This is the 'admin.list_users' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Base query
    query = User.query

    # Search functionality
    search_query = request.args.get('search', '').strip()
    if search_query:
        query = query.filter(
            db.or_(
                User.username.ilike(f"%{search_query}%"),
                User.email.ilike(f"%{search_query}%"),
                User.phone.ilike(f"%{search_query}%")
            )
        )

    # Paginate results
    users_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = users_pagination.items

    return render_template('admin/users/list.html',
                           users=users,
                           users_pagination=users_pagination,
                           search_query=search_query)


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
def toggle_user_active(user_id):
    """
    Toggle user's active status (block/unblock).
    This is the 'admin.toggle_user_active' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    user = User.query.get_or_404(user_id)
    # Prevent admin from toggling their own status
    if user.id == current_user.id:
        flash('You cannot change your own status.', 'danger')
        return redirect(url_for('admin.list_users'))

    user.is_active = not user.is_active
    db.session.commit()

    status_msg = "activated" if user.is_active else "deactivated"
    flash(f'User {user.username} has been {status_msg}.', 'success')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """
    Delete a user.
    This is the 'admin.delete_user' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    user = User.query.get_or_404(user_id)
    # Prevent admin from deleting themselves or other admins (optional)
    if user.id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('admin.list_users'))
    if user.is_admin:  # Assuming you have an is_admin flag on User
        flash('Cannot delete admin user.', 'danger')
        return redirect(url_for('admin.list_users'))

    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')

    return redirect(url_for('admin.list_users'))