import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from ..models.user import User


# ============================================
# FUNÇÕES DE VALIDAÇÃO PERSONALIZADAS
# ============================================

def validate_angola_phone(form, field):
    """Valida número de telefone angolano."""
    phone = field.data
    if phone:
        # Remove espaços e caracteres especiais
        phone_clean = re.sub(r'[\s\+\(\)\-]', '', phone)
        
        # Padrões para números angolanos:
        # 923456789 (9 dígitos, começa com 9)
        # +244923456789 ou 00244923456789
        patterns = [
            r'^9[0-9]{8}$',           # 923456789
            r'^2449[0-9]{8}$',        # 244923456789
            r'^002449[0-9]{8}$',      # 00244923456789
            r'^\+2449[0-9]{8}$'       # +244923456789
        ]
        
        for pattern in patterns:
            if re.match(pattern, phone_clean):
                # Normalizar para formato padrão: 923456789
                field.data = phone_clean[-9:]
                return
        
        raise ValidationError('Número de telefone inválido. Use formato: 923456789 ou +244923456789')


# ============================================
# FORMULÁRIOS
# ============================================

class LoginForm(FlaskForm):
    """Formulário de login (aceita email OU telefone)."""
    email_or_phone = StringField('Email ou Telefone', validators=[
        DataRequired(message='Email ou telefone é obrigatório')
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória')
    ])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')
    
    def validate_email_or_phone(self, field):
        """Valida se o campo é email ou telefone válido."""
        value = field.data.strip()
        
        # Verificar se é email (contém @)
        if '@' in value:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValidationError('Email inválido')
        else:
            # Verificar se é telefone angolano válido
            phone_clean = re.sub(r'[\s\+\(\)\-]', '', value)
            
            # Padrões para números angolanos
            patterns = [
                r'^9[0-9]{8}$',           # 923456789
                r'^2449[0-9]{8}$',        # 244923456789
                r'^002449[0-9]{8}$',      # 00244923456789
                r'^\+2449[0-9]{8}$'       # +244923456789
            ]
            
            is_valid_phone = False
            for pattern in patterns:
                if re.match(pattern, phone_clean):
                    is_valid_phone = True
                    break
            
            if not is_valid_phone:
                raise ValidationError('Número de telefone inválido. Use formato: 923456789')


class RegistrationForm(FlaskForm):
    """Formulário de registo de novo utilizador."""
    name = StringField('Nome completo', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=100, message='Nome deve ter entre 3 e 100 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido'),
        Length(max=120)
    ])
    phone = StringField('Telefone', validators=[
        Optional(),
        validate_angola_phone  # ← AGORA ESTÁ DEFINIDA ANTES
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=6, message='Senha deve ter pelo menos 6 caracteres')
    ])
    password_confirm = PasswordField('Confirmar senha', validators=[
        DataRequired(message='Confirme sua senha'),
        EqualTo('password', message='As senhas não coincidem')
    ])
    user_type = SelectField('Tipo de utilizador', choices=[
        ('tenant', 'Inquilino - Procuro casa'),
        ('landlord', 'Senhorio - Tenho imóveis para arrendar')
    ], validators=[DataRequired(message='Selecione o tipo de utilizador')])
    
    submit = SubmitField('Criar conta')
    
    def validate_email(self, field):
        """Verifica se o email já está registado."""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Este email já está registado. Faça login ou use outro email.')
    
    def validate_phone(self, field):
        """Verifica se o telefone já está registado (se fornecido)."""
        if field.data:
            # Normalizar telefone
            phone_clean = re.sub(r'[\s\+\(\)\-]', '', field.data)
            phone_normalized = phone_clean[-9:] if len(phone_clean) >= 9 else phone_clean
            
            existing_user = User.query.filter_by(phone=phone_normalized).first()
            if existing_user:
                raise ValidationError('Este número de telefone já está registado.')