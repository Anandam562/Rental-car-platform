# routes/admin/documents.py
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import admin_bp
from models import db
from models.document import Document  # Assuming Document model exists


@admin_bp.route('/documents')
@login_required
def list_documents():
    """List all user documents"""
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('car.home'))

    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Document.query.join(Document.user)

    search_query = request.args.get('search', '').strip()
    if search_query:
        query = query.filter(
            db.or_(
                Document.document_type.ilike(f"%{search_query}%"),
                Document.user.username.ilike(f"%{search_query}%"),
                Document.user.email.ilike(f"%{search_query}%")
                # Add more searchable fields as needed
            )
        )

    documents_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    documents = documents_pagination.items

    return render_template('admin/documents/list.html',
                           documents=documents,
                           documents_pagination=documents_pagination,
                           search_query=search_query)


@admin_bp.route('/documents/<int:doc_id>/verify', methods=['POST'])
@login_required
def verify_document(doc_id):
    """Verify a user document"""
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('car.home'))

    doc = Document.query.get_or_404(doc_id)
    doc.is_verified = True
    from datetime import datetime
    doc.verified_at = datetime.utcnow()
    db.session.commit()

    flash(f'Document for user {doc.user.username} verified successfully.', 'success')
    return redirect(url_for('admin.list_documents'))


@admin_bp.route('/documents/<int:doc_id>/reject', methods=['POST'])
@login_required
def reject_document(doc_id):
    """Reject a user document"""
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('car.home'))

    doc = Document.query.get_or_404(doc_id)
    doc.is_verified = False
    doc.verified_at = None  # Clear verification timestamp
    # Optionally add a rejection reason
    # doc.rejection_reason = request.form.get('reason', '')
    db.session.commit()

    flash(f'Document for user {doc.user.username} rejected.', 'success')
    return redirect(url_for('admin.list_documents'))

# Add routes for viewing document details, downloading, etc.