from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import relationship

from .favorite import Favorite

from ..extensions import db, bcrypt


class User(UserMixin, db.Model):
    """Utilizador da plataforma (senhorio ou inquilino)."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Verificação - CORRIGIDO: default é 'none', NÃO 'pending'
    is_verified = db.Column(db.Boolean, default=False)
    is_landlord = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Documentos para verificação
    bi_photo = db.Column(db.String(200))
    bi_front_photo = db.Column(db.String(200))
    bi_back_photo = db.Column(db.String(200))
    property_document = db.Column(db.String(200))
    
    # Status de verificação - CORRIGIDO: default='none'
    verification_status = db.Column(db.String(20), default='none')  # none, pending, approved, rejected
    verification_rejection_reason = db.Column(db.String(500))
    verification_requested_at = db.Column(db.DateTime)
    verification_processed_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Reputação
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)

    # Suspensão
    is_active = db.Column(db.Boolean, default=True)
    
    # Estatísticas
    properties_count = db.Column(db.Integer, default=0)
    successful_deals = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relacionamentos
    properties = relationship('Property', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    sent_messages = relationship('Message', foreign_keys='Message.sender_id', back_populates='sender', lazy='dynamic', cascade='all, delete-orphan')
    received_messages = relationship('Message', foreign_keys='Message.receiver_id', back_populates='receiver', lazy='dynamic', cascade='all, delete-orphan')
    given_reviews = relationship('Review', foreign_keys='Review.reviewer_id', back_populates='reviewer', lazy='dynamic', cascade='all, delete-orphan')
    received_reviews = relationship('Review', foreign_keys='Review.reviewed_id', back_populates='reviewed', lazy='dynamic', cascade='all, delete-orphan')
    favorites = relationship('Favorite', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Pedido de mudança de papel (inquilino -> senhorio)
    requested_role = db.Column(db.String(20), nullable=True)  # 'landlord' ou None
    role_request_date = db.Column(db.DateTime, nullable=True)
    role_request_notes = db.Column(db.String(500), nullable=True)  # Justificação do utilizador

    def set_password(self, password):
        """Faz hash da senha antes de guardar."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verifica se a senha está correta."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def update_rating(self):
        """Atualiza a média de avaliações do utilizador."""
        from .review import Review
        avg = db.session.query(db.func.avg(Review.rating)).filter(
            Review.reviewed_id == self.id
        ).scalar()
        
        count = db.session.query(db.func.count(Review.id)).filter(
            Review.reviewed_id == self.id
        ).scalar()
        
        self.rating = float(avg) if avg else 0.0
        self.total_reviews = count or 0
        db.session.commit()
    
    def unread_messages_count(self):
        """Retorna número de mensagens não lidas."""
        from .message import Message
        return Message.query.filter_by(receiver_id=self.id, read=False).count()
    
    def can_publish_more_properties(self):
        """Verifica se o utilizador pode publicar mais imóveis."""
        from flask import current_app
        
        if self.is_verified:
            max_properties = current_app.config.get('MAX_PROPERTIES_VERIFIED', 10)
        else:
            max_properties = current_app.config.get('MAX_PROPERTIES_UNVERIFIED', 1)
        
        return self.properties_count < max_properties
    
    def to_dict(self):
        """Converte o utilizador para dicionário (API)."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'is_verified': self.is_verified,
            'is_landlord': self.is_landlord,
            'rating': self.rating,
            'total_reviews': self.total_reviews,
            'successful_deals': self.successful_deals,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'

    def get_received_reviews(self, limit=10):
        """Retorna as avaliações recebidas."""
        from .review import Review
        return Review.query.filter_by(
            reviewed_id=self.id, 
            is_visible=True
        ).order_by(Review.created_at.desc()).limit(limit).all()
    
    def get_average_rating(self):
        """Calcula a média das avaliações."""
        from .review import Review
        from sqlalchemy import func
        
        result = db.session.query(func.avg(Review.rating)).filter(
            Review.reviewed_id == self.id,
            Review.is_visible == True
        ).scalar()
        
        return float(result) if result else 0.0
    
    def get_rating_count(self):
        """Retorna o número de avaliações recebidas."""
        from .review import Review
        return Review.query.filter_by(reviewed_id=self.id, is_visible=True).count()

    def get_favorites(self):
        """Retorna os imóveis favoritos do utilizador."""
        from .property import Property
        from .favorite import Favorite
        return Property.query.join(Favorite).filter(Favorite.user_id == self.id).all()
    
    def is_favorite(self, property_id):
        """Verifica se um imóvel está nos favoritos."""
        from .favorite import Favorite
        return Favorite.query.filter_by(user_id=self.id, property_id=property_id).first() is not None
    
    def add_favorite(self, property_id):
        """Adiciona um imóvel aos favoritos."""
        from .favorite import Favorite
        if not self.is_favorite(property_id):
            favorite = Favorite(user_id=self.id, property_id=property_id)
            db.session.add(favorite)
            db.session.commit()
            return True
        return False
    
    def remove_favorite(self, property_id):
        """Remove um imóvel dos favoritos."""
        from .favorite import Favorite
        favorite = Favorite.query.filter_by(user_id=self.id, property_id=property_id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return True
        return False