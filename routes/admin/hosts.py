# routes/admin/hosts.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import admin_bp
from models import db
from models.host import Host
from models.user import User


@admin_bp.route('/hosts')
@login_required
def list_hosts():
    """
    List all hosts with search and pagination.
    This is the 'admin.list_hosts' endpoint.
    """
    # Authorization check
    if not current_user.has_access('content'):  # Or 'support', 'finance', 'super'
        flash('Access denied: Insufficient permissions.', 'error')
        return redirect(url_for('admin.dashboard'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Base query - Join with User for username/email
    query = Host.query.join(Host.user)

    # Search functionality
    search_query = request.args.get('search', '').strip()
    if search_query:
        query = query.filter(
            db.or_(
                Host.company_name.ilike(f"%{search_query}%"),
                User.username.ilike(f"%{search_query}%"),
                User.email.ilike(f"%{search_query}%"),
                User.phone.ilike(f"%{search_query}%"),
                Host.phone.ilike(f"%{search_query}%")
            )
        )

    # Paginate results
    hosts_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    hosts = hosts_pagination.items

    return render_template('admin/hosts/list.html',
                           hosts=hosts,
                           hosts_pagination=hosts_pagination,
                           search_query=search_query)


@admin_bp.route('/hosts/<int:host_id>/verify', methods=['POST'])
@login_required
def verify_host(host_id):
    """
    Verify a host.
    This is the 'admin.verify_host' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    host = Host.query.get_or_404(host_id)
    host.is_verified = True
    db.session.commit()

    flash(f'Host {host.company_name or host.user.username} verified successfully.', 'success')
    return redirect(url_for('admin.list_hosts'))


@admin_bp.route('/hosts/<int:host_id>/unverify', methods=['POST'])
@login_required
def unverify_host(host_id):
    """
    Unverify a host.
    This is the 'admin.unverify_host' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    host = Host.query.get_or_404(host_id)
    host.is_verified = False
    db.session.commit()

    flash(f'Host {host.company_name or host.user.username} unverified.', 'success')
    return redirect(url_for('admin.list_hosts'))


@admin_bp.route('/hosts/<int:host_id>/toggle-active', methods=['POST'])
@login_required
def toggle_host_active(host_id):
    """
    Toggle host's active status (block/unblock).
    This is the 'admin.toggle_host_active' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    host = Host.query.get_or_404(host_id)

    # Toggle the user's is_active status (assuming Host is linked to User)
    if host.user:
        host.user.is_active = not host.user.is_active
        db.session.commit()

        status_msg = "activated" if host.user.is_active else "deactivated"
        flash(f'Host {host.company_name or host.user.username} has been {status_msg}.', 'success')
    else:
        flash('Host user not found.', 'danger')

    return redirect(url_for('admin.list_hosts'))


@admin_bp.route('/hosts/<int:host_id>/delete', methods=['POST'])
@login_required
def delete_host(host_id):
    """
    Delete a host (and associated user if desired).
    This is the 'admin.delete_host' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    host = Host.query.get_or_404(host_id)

    try:
        host_name = host.company_name or host.user.username
        user_id = host.user_id  # Store user ID before deleting host

        # Delete the host profile
        db.session.delete(host)
        db.session.commit()

        # Optionally, delete the associated user account
        # user = User.query.get(user_id)
        # if user:
        #     db.session.delete(user)
        #     db.session.commit()

        flash(f'Host {host_name} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting host: {str(e)}', 'danger')

    return redirect(url_for('admin.list_hosts'))