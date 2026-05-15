from datetime import datetime
from sqlalchemy.orm import relationship

from ..extensions import db


class Message(db.Model):
    """Mensagem entre utilizadores."""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Chaves estrangeiras
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False, index=True)
    
    # Relacionamentos
    sender = relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    receiver = relationship('User', foreign_keys=[receiver_id], back_populates='received_messages')
    property = relationship('Property', back_populates='messages')
    
    def mark_as_read(self):
        """Marca a mensagem como lida."""
        if not self.read:
            self.read = True
            db.session.commit()
    
    def to_dict(self):
        """Converte a mensagem para dicionário (API)."""
        return {
            'id': self.id,
            'content': self.content,
            'read': self.read,
            'sender_id': self.sender_id,
            'sender_name': self.sender.name if self.sender else None,
            'receiver_id': self.receiver_id,
            'property_id': self.property_id,
            'property_title': self.property.title if self.property else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Message {self.sender_id} -> {self.receiver_id}>'