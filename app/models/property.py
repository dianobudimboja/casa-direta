from datetime import datetime
from sqlalchemy.orm import relationship

from ..extensions import db


class Property(db.Model):
    """Imóvel publicado para arrendamento."""
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Detalhes do imóvel
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(200), nullable=False, index=True)
    address = db.Column(db.String(300))
    neighborhood = db.Column(db.String(100))  # Bairro (Kilamba, Camama, etc)
    
    bedrooms = db.Column(db.Integer, default=1)
    bathrooms = db.Column(db.Integer, default=1)
    area = db.Column(db.Float)  # Área em m²
    
    # Fotos
    photos = db.Column(db.JSON, default=list)  # Lista de caminhos das fotos
    main_photo = db.Column(db.String(200))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)  # Destaque pago
    
    # Estatísticas
    views = db.Column(db.Integer, default=0)
    inquiries = db.Column(db.Integer, default=0)  # Mensagens recebidas
    
    # Sistema anti-intermediário
    suspicion_score = db.Column(db.Integer, default=0)  # 0-100
    requires_review = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Data de expiração do anúncio
    
    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Relacionamentos
    owner = relationship('User', back_populates='properties')
    messages = relationship('Message', back_populates='property', lazy='dynamic', cascade='all, delete-orphan')
    favorited_by = relationship('Favorite', back_populates='property', lazy='dynamic')

    # Coordenadas para o mapa
    latitude = db.Column(db.Float, nullable=True)   # -90 a 90
    longitude = db.Column(db.Float, nullable=True)  # -180 a 180
    
    def increment_views(self):
        """Incrementa o contador de visualizações."""
        self.views += 1
        db.session.commit()
    
    def increment_inquiries(self):
        """Incrementa o contador de mensagens."""
        self.inquiries += 1
        db.session.commit()
    
    def update_suspicion_score(self, score):
        """Atualiza o score de suspeição e marca para revisão se necessário."""
        self.suspicion_score = score
        self.requires_review = score >= 60
        db.session.commit()
    
    def is_expired(self):
        """Verifica se o anúncio expirou."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def to_dict(self):
        """Converte o imóvel para dicionário (API)."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'location': self.location,
            'neighborhood': self.neighborhood,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'area': self.area,
            'main_photo': self.main_photo,
            'photos': self.photos or [],
            'is_verified': self.is_verified,
            'is_featured': self.is_featured,
            'views': self.views,
            'inquiries': self.inquiries,
            'owner_name': self.owner.name if self.owner else None,
            'owner_rating': self.owner.rating if self.owner else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Property {self.title} - {self.price}>'

    def favorites_count(self):
        """Número de vezes que foi adicionado aos favoritos."""
        return self.favorited_by.count()

    def has_coordinates(self):
        """Verifica se o imóvel tem coordenadas válidas."""
        return self.latitude is not None and self.longitude is not None