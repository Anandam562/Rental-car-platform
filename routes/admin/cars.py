# routes/admin/cars.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import admin_bp
from models import db
from models.car import Car
from models.host import Host


@admin_bp.route('/cars')
@login_required
def list_cars():
    """
    List all cars with search and pagination.
    This is the 'admin.list_cars' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Base query - Join with Host and User for host info
    query = Car.query.join(Car.host).join(Host.user)

    # Search functionality
    search_query = request.args.get('search', '').strip()
    if search_query:
        query = query.filter(
            db.or_(
                Car.make.ilike(f"%{search_query}%"),
                Car.model.ilike(f"%{search_query}%"),
                Car.city.ilike(f"%{search_query}%"),
                Car.locality.ilike(f"%{search_query}%"),
                Car.full_address.ilike(f"%{search_query}%"),
                Host.company_name.ilike(f"%{search_query}%"),
                Host.user.username.ilike(f"%{search_query}%")
            )
        )

    # Paginate results
    cars_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    cars = cars_pagination.items

    return render_template('admin/cars/list.html',
                           cars=cars,
                           cars_pagination=cars_pagination,
                           search_query=search_query)


@admin_bp.route('/cars/<int:car_id>/toggle-block', methods=['POST'])
@login_required
def toggle_car_block(car_id):
    """
    Block/Unblock a car.
    This is the 'admin.toggle_car_block' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    car = Car.query.get_or_404(car_id)

    car.is_blocked = not car.is_blocked
    # Optionally set a timestamp and reason
    from datetime import datetime
    car.blocked_at = datetime.utcnow() if car.is_blocked else None
    car.blocked_reason = request.form.get('reason', 'Blocked by admin') if car.is_blocked else None

    db.session.commit()

    status_msg = "blocked" if car.is_blocked else "unblocked"
    flash(f'Car {car.make} {car.model} has been {status_msg}.', 'success')
    return redirect(url_for('admin.list_cars'))


@admin_bp.route('/cars/<int:car_id>/delete', methods=['POST'])
@login_required
def delete_car(car_id):
    """
    Delete a car.
    This is the 'admin.delete_car' endpoint.
    """
    # Authorization check
    if not hasattr(current_user, 'is_super_admin'):
        flash('Access denied.')
        return redirect(url_for('car.home'))

    car = Car.query.get_or_404(car_id)

    try:
        car_name = f"{car.make} {car.model}"

        # Delete associated images first (filesystem cleanup)
        for image in car.images:
            filepath = os.path.join('static', 'uploads', image.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            db.session.delete(image)

        # Delete the car
        db.session.delete(car)
        db.session.commit()

        flash(f'Car {car_name} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting car: {str(e)}', 'danger')

    return redirect(url_for('admin.list_cars'))