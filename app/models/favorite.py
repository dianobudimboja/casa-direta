# app/models/favorite.py
from datetime import datetime
from sqlalchemy.orm import relationship

from ..extensions import db


class Favorite(db.Model):
    """Imóvel favorito de um utilizador."""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = relationship('User', back_populates='favorites')
    property = relationship('Property', back_populates='favorited_by')
    
    def __repr__(self):
        return f'<Favorite user={self.user_id} property={self.property_id}>'