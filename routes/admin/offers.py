# routes/admin/offers.py
# ... (imports) ...
from flask_login import login_required

from routes.admin import admin_bp
from utils.notification_sender import send_notification_to_user # Import notification sender
# ... (blueprint definition) ...

@admin_bp.route('/offers/create', methods=['POST']) # Example endpoint
@login_required
def create_offer():
    # ... (admin authorization check) ...
    # ... (offer creation logic) ...

    # Example: Send notification to all users
    # In practice, you might segment users or target specific ones
    from models.user import User
    all_users = User.query.all()
    offer_message = f"New offer available: {offer_details}!" # Construct message
    for user in all_users:
        send_notification_to_user(user_id=user.id, message=offer_message)

    flash('Offer created and notifications sent!', 'success')
    return redirect(url_for('admin.list_offers')) # Example redirect
# ... (rest of routes) ...