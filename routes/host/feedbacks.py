# routes/host/feedbacks.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
# Import HostFeedback for feedback listing
from models.host_feedback import HostFeedback
# Import Host to access host profile
from models.host import Host

# Import the host blueprint object from the package's __init__.py
# Make sure this import path matches your project structure
from routes.host import host_bp

@host_bp.route('/feedbacks')
@login_required
def feedbacks():
    """
    Display host's feedback.
    This creates the 'host.feedbacks' endpoint.
    """
    # --- Fetch Host Profile ---
    # Get the host profile associated with the current user
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()
    # --- End Fetch Host Profile ---

    # --- Fetch Feedbacks ---
    # Get feedback for this host, ordered by timestamp descending (newest first)
    # Implement pagination if needed for large lists
    page = request.args.get('page', 1, type=int)
    per_page = 5 # Number of feedbacks per page

    feedbacks_query = HostFeedback.query.filter_by(
        host_id=host.id # Belongs to current host
    ).order_by(
        HostFeedback.created_at.desc() # Order by timestamp (newest first)
    )

    feedbacks_pagination = feedbacks_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    feedbacks = feedbacks_pagination.items
    # --- End Fetch Feedbacks ---

    # --- Count Unresolved Feedbacks ---
    # Example: Count unresolved feedbacks
    unresolved_count = HostFeedback.query.filter_by(
        host_id=host.id,
        is_resolved=False
    ).count()
    # --- End Count Unresolved Feedbacks ---

    # --- Prepare Context for Template ---
    context = {
        'host': host, # Pass the host object
        'feedbacks': feedbacks, # Pass the list of feedbacks
        'feedbacks_pagination': feedbacks_pagination, # Pass the pagination object
        'unresolved_count': unresolved_count # Pass the count of unresolved feedbacks
    }
    # --- End Context ---

    # --- Render Template ---
    return render_template('host/feedbacks/list.html', **context)
    # --- End Render ---

# --- NEW: Mark Feedback as Resolved Route ---
@host_bp.route('/feedbacks/<int:feedback_id>/resolve', methods=['POST'])
@login_required
def resolve_feedback(feedback_id):
    """
    Mark a specific feedback as resolved by the host.
    This creates the 'host.resolve_feedback' endpoint.
    """
    # --- Fetch Host Profile ---
    # Get the host profile associated with the current user
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()
    # --- End Fetch Host Profile ---

    # --- Fetch Feedback ---
    # Get the feedback by ID and ensure it belongs to the current host
    feedback = HostFeedback.query.join(HostFeedback.host).filter(
        HostFeedback.id == feedback_id,
        Host.id == host.id
    ).first_or_404()
    # --- End Fetch Feedback ---

    # --- Mark Feedback as Resolved ---
    if not feedback.is_resolved:
        feedback.is_resolved = True
        db.session.commit()
        flash('Feedback marked as resolved.', 'success')
    else:
        flash('Feedback was already resolved.', 'info')
    # --- End Mark Feedback as Resolved ---

    # --- Redirect ---
    # Redirect back to the feedback list page, preserving the current page number
    page = request.args.get('page', 1, type=int)
    return redirect(url_for('host.feedbacks', page=page))
    # --- End Redirect ---
# --- END NEW: Mark Feedback as Resolved Route ---
# --- End Host Feedback Routes ---