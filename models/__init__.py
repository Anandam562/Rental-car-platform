from flask_sqlalchemy import SQLAlchemy

# Create db instance here - this will be imported by other modules
db = SQLAlchemy()

# Don't import models here to avoid circular imports
# Models will import db from this module