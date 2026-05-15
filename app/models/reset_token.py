from datetime import datetime, timedelta
import secrets
from ..extensions import db


class PasswordResetToken(db.Model):
    """Token para recuperação de senha."""
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)
    
    # Relacionamento
    user = db.relationship('User', backref='reset_tokens')
    
    @classmethod
    def create_token(cls, user_id, expires_in_hours=1):
        """Cria um novo token de recuperação."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        reset_token = cls(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(reset_token)
        db.session.commit()
        
        return token
    
    @classmethod
    def verify_token(cls, token):
        """Verifica se o token é válido e retorna o user_id."""
        reset_token = cls.query.filter_by(token=token, used=False).first()
        
        if not reset_token:
            return None
        
        if reset_token.expires_at < datetime.utcnow():
            return None
        
        return reset_token.user_id
    
    def mark_as_used(self):
        """Marca o token como usado."""
        self.used = True
        db.session.commit()