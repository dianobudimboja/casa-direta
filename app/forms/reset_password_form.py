from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from ..models.user import User


class ForgotPasswordForm(FlaskForm):
    """Formulário para solicitar recuperação de senha."""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    submit = SubmitField('Enviar link de recuperação')
    
    def validate_email(self, field):
        """Verifica se o email existe na base de dados."""
        user = User.query.filter_by(email=field.data).first()
        if not user:
            raise ValidationError('Nenhum utilizador encontrado com este email.')


class ResetPasswordForm(FlaskForm):
    """Formulário para redefinir a senha."""
    password = PasswordField('Nova senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres')
    ])
    confirm_password = PasswordField('Confirmar nova senha', validators=[
        DataRequired(message='Confirme sua senha'),
        EqualTo('password', message='As senhas não coincidem')
    ])
    submit = SubmitField('Redefinir senha')