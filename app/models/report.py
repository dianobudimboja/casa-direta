from datetime import datetime
from sqlalchemy.orm import relationship

from ..extensions import db


class Report(db.Model):
    """Denúncia de um imóvel suspeito."""
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(50), nullable=False)  # fraude, spam, ofensivo, outro
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    admin_notes = db.Column(db.Text)
    
    # Chaves estrangeiras
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    
    # Relacionamentos
    reporter = relationship('User', foreign_keys=[reporter_id], backref='reports_made')
    property = relationship('Property', backref='reports')
    admin = relationship('User', foreign_keys=[processed_by], backref='reports_processed')
    
    def to_dict(self):
        return {
            'id': self.id,
            'reason': self.reason,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'reporter_name': self.reporter.name if self.reporter else None,
            'property_title': self.property.title if self.property else None
        }
    
    def __repr__(self):
        return f'<Report {self.id}: {self.reason}>'