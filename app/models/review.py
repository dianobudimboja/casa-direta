from datetime import datetime
from sqlalchemy.orm import relationship

from ..extensions import db


class Review(db.Model):
    """Avaliação de um utilizador por outro."""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # 1 a 5 estrelas
    comment = db.Column(db.Text)
    is_visible = db.Column(db.Boolean, default=True)  # Admin pode ocultar
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Chaves estrangeiras
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    reviewed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    
    # Relacionamentos
    reviewer = relationship('User', foreign_keys=[reviewer_id], back_populates='given_reviews')
    reviewed = relationship('User', foreign_keys=[reviewed_id], back_populates='received_reviews')
    property = relationship('Property')
    
    def to_dict(self):
        """Converte a avaliação para dicionário."""
        return {
            'id': self.id,
            'rating': self.rating,
            'comment': self.comment,
            'reviewer_id': self.reviewer_id,
            'reviewer_name': self.reviewer.name if self.reviewer else None,
            'reviewed_id': self.reviewed_id,
            'reviewed_name': self.reviewed.name if self.reviewed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Review {self.reviewer_id} -> {self.reviewed_id}: {self.rating}/5>'