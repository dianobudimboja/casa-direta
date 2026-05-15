from datetime import datetime
from sqlalchemy.orm import relationship

from ..extensions import db


class Contract(db.Model):
    """Contrato de arrendamento entre senhorio e inquilino."""
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados do imóvel
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    property_title = db.Column(db.String(200), nullable=False)
    property_address = db.Column(db.String(300), nullable=False)
    property_rent = db.Column(db.Float, nullable=False)
    
    # Dados do senhorio
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    landlord_name = db.Column(db.String(100), nullable=False)
    landlord_bi = db.Column(db.String(50))
    landlord_phone = db.Column(db.String(20))
    
    # Dados do inquilino
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    tenant_name = db.Column(db.String(100), nullable=False)
    tenant_bi = db.Column(db.String(50))
    tenant_phone = db.Column(db.String(20))
    
    # Condições do contrato
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    payment_day = db.Column(db.Integer, default=5)
    security_deposit = db.Column(db.Float, default=0)  # Caução
    
    # Cláusulas personalizadas
    additional_clauses = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, signed_by_landlord, signed_by_tenant, completed, cancelled
    
    # PDF
    pdf_path = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    signed_at = db.Column(db.DateTime)
    
    # Relacionamentos
    property = relationship('Property', backref='contracts')
    landlord = relationship('User', foreign_keys=[landlord_id], backref='landlord_contracts')
    tenant = relationship('User', foreign_keys=[tenant_id], backref='tenant_contracts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'property_title': self.property_title,
            'property_address': self.property_address,
            'property_rent': self.property_rent,
            'landlord_name': self.landlord_name,
            'tenant_name': self.tenant_name,
            'start_date': self.start_date.strftime('%d/%m/%Y'),
            'end_date': self.end_date.strftime('%d/%m/%Y'),
            'status': self.status
        }
    
    def __repr__(self):
        return f'<Contract {self.id}: {self.property_title}>'