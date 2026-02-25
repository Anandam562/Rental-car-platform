# routes/host/ratings.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
# Import HostRating for ratings listing
from models.host_rating import HostRating
# Import Host to access host profile
from models.host import Host
# Import Booking if needed for related info
# from models.booking import Booking

# Import the host blueprint object from the package's __init__.py
# Make sure this import path matches your project structure
from routes.host import host_bp

@host_bp.route('/ratings')
@login_required
def ratings():
    """
    Display host's ratings and reviews.
    This creates the 'host.ratings' endpoint.
    """
    # --- Fetch Host Profile ---
    # Get the host profile associated with the current user
    host = Host.query.filter_by(user_id=current_user.id).first_or_404()
    # --- End Fetch Host Profile ---

    # --- Fetch Ratings ---
    # Get ratings for this host, ordered by timestamp descending (newest first)
    # Implement pagination if needed for large lists
    page = request.args.get('page', 1, type=int)
    per_page = 5 # Number of ratings per page

    ratings_query = HostRating.query.filter_by(
        host_id=host.id # Belongs to current host
    ).order_by(
        HostRating.created_at.desc() # Order by timestamp (newest first)
    )

    ratings_pagination = ratings_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    ratings = ratings_pagination.items
    # --- End Fetch Ratings ---

    # --- Calculate Average Rating ---
    # Example: Calculate average rating
    if ratings:  # <-- Check if ratings list is NOT empty
        total_rating = sum(r.rating for r in ratings)
        average_rating = round(total_rating / len(ratings), 1)
    else:
        average_rating = 0.0  # <-- Set to 0.0 if no ratings
    # --- End Calculate Average Rating ---

    # ...
    # --- Calculate Rating Distribution ---
    # Example: Count ratings by star value (1-5)
    from collections import Counter
    rating_counts = Counter(r.rating for r in ratings)
    rating_distribution = {
        5: rating_counts.get(5, 0),
        4: rating_counts.get(4, 0),
        3: rating_counts.get(3, 0),
        2: rating_counts.get(2, 0),
        1: rating_counts.get(1, 0),
    }
    # --- End Calculate Rating Distribution ---

    # --- Prepare Context for Template ---
    context = {
        # ...
        'ratings': ratings,  # Pass the list of ratings
        'ratings_pagination': ratings_pagination,  # Pass the pagination object
        'average_rating': average_rating,  # Pass the average rating
        'rating_distribution': rating_distribution,  # Pass the rating distribution
        'total_ratings': len(ratings)  # <-- Pass the total number of ratings
    }
    # --- End Context ---
    # ...
    # --- Render Template ---
    return render_template('host/ratings/list.html', **context)
    # --- End Render ---
# --- End Host Ratings Route ---