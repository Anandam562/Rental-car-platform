# models/document.py
from . import db
from datetime import datetime


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    # --- CRITICAL: Specify the type of document ---
    document_type = db.Column(db.String(50), nullable=False)  # e.g., 'rc', 'license', 'dl', 'insurance'
    # --- END CRITICAL ---
    is_verified = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)

    # --- CRITICAL: The Foreign Key linking this document to its OWNER (User or Host) ---
    # This is the column used for the Document.user relationship
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # --- END CRITICAL ---

    # --- Optional: Link to Car if document is car-specific ---
    # car_id = db.Column(db.Integer, db.ForeignKey('cars.id'))
    # car = db.relationship('Car', backref='documents')
    # --- End Optional ---

    # --- CRITICAL FIX: Explicitly define the relationship with foreign_keys ---
    # BEFORE (Ambiguous):
    # user = db.relationship('User', backref='documents')

    # AFTER (Explicit foreign_keys):
    # Tell SQLAlchemy: "Use the 'user_id' column to link Document to User"
    user = db.relationship('User', foreign_keys=[user_id], backref='documents_uploaded')

    # Note: Changed backref name to 'documents_uploaded' to avoid potential conflicts
    # with other User.document relationships (like rc_document, dl_document if they exist on User)
    # --- END CRITICAL FIX ---

    def __repr__(self):
        return f'<Document {self.filename} ({self.document_type}) for User {self.user_id}>'

    # --- Optional: Helper methods ---
    def verify(self):
        """Mark document as verified."""
        self.is_verified = True
        self.verified_at = datetime.utcnow()
        db.session.add(self)
        # Don't commit here, let caller handle it

    def belongs_to(self, user_obj):
        """Check if document belongs to a specific user."""
        return self.user_id == user_obj.id
    # --- End Optional ---
