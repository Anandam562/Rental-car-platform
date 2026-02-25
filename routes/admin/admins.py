# routes/admin/admins.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import admin_bp
from models import db
from models.admin import Admin


@admin_bp.route('/admins')
@login_required
def list_admins():
    """List all admins (super admin only)"""
    # Authorization check (ensure user is a super admin)
    if not (hasattr(current_user, 'access_level') and current_user.can_manage_admins()):
        flash('Access denied. Only super admins can manage admins.')
        return redirect(url_for('admin.dashboard'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Base query
    query = Admin.query

    # Search functionality
    search_query = request.args.get('search', '').strip()
    if search_query:
        query = query.filter(
            db.or_(
                Admin.username.ilike(f"%{search_query}%"),
                Admin.email.ilike(f"%{search_query}%"),
                Admin.access_level.ilike(f"%{search_query}%")
            )
        )

    admins_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    admins = admins_pagination.items

    return render_template('admin/admins/list.html',
                           admins=admins,
                           admins_pagination=admins_pagination,
                           search_query=search_query)


@admin_bp.route('/admins/<int:admin_id>/toggle-active', methods=['POST'])
@login_required
def toggle_admin_active(admin_id):
    """Toggle admin's active status (super admin only)"""
    # Authorization check
    if not (hasattr(current_user, 'access_level') and current_user.can_manage_admins()):
        flash('Access denied. Only super admins can manage admins.')
        return redirect(url_for('admin.dashboard'))

    # Prevent admin from toggling their own status
    if admin_id == current_user.id:
        flash('You cannot change your own status.', 'danger')
        return redirect(url_for('admin.list_admins'))

    admin = Admin.query.get_or_404(admin_id)
    admin.is_active = not admin.is_active
    db.session.commit()

    status_msg = "activated" if admin.is_active else "deactivated"
    flash(f'Admin {admin.username} has been {status_msg}.', 'success')
    return redirect(url_for('admin.list_admins'))


@admin_bp.route('/admins/<int:admin_id>/delete', methods=['POST'])
@login_required
def delete_admin(admin_id):
    """Delete an admin (super admin only)"""
    # Authorization check
    if not (hasattr(current_user, 'access_level') and current_user.can_manage_admins()):
        flash('Access denied. Only super admins can manage admins.')
        return redirect(url_for('admin.dashboard'))

    # Prevent admin from deleting themselves
    if admin_id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('admin.list_admins'))

    admin = Admin.query.get_or_404(admin_id)
    # Prevent deletion of other super admins?
    # if admin.access_level == 'super' and admin.id != current_user.id:
    #     flash('Cannot delete other super admins.', 'danger')
    #     return redirect(url_for('admin.list_admins'))

    try:
        username = admin.username
        db.session.delete(admin)
        db.session.commit()
        flash(f'Admin {username} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting admin: {str(e)}', 'danger')

    return redirect(url_for('admin.list_admins'))
