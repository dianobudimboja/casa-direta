from flask import Blueprint, render_template, redirect, url_for, flash, request
from datetime import datetime

from ..extensions import db
from ..models.user import User
from ..models.reset_token import PasswordResetToken
from ..forms.reset_password_form import ForgotPasswordForm, ResetPasswordForm
from ..services.email_service import send_reset_email

bp = Blueprint('password', __name__, url_prefix='/password')


@bp.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    """Página para solicitar recuperação de senha."""
    
    if request.method == 'GET':
        form = ForgotPasswordForm()
        return render_template('auth/forgot_password.html', form=form)
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # Cria token de recuperação
            token = PasswordResetToken.create_token(user.id)
            
            # Envia email
            try:
                send_reset_email(user, token)
                flash('Um email com instruções de recuperação foi enviado para o seu endereço.', 'success')
            except Exception as e:
                flash('Erro ao enviar email. Tente novamente mais tarde.', 'danger')
                print(f"Erro ao enviar email: {e}")
        else:
            flash('Se o email existir, você receberá as instruções.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)


@bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Página para redefinir a senha com token."""
    
    # Verifica se o token é válido
    user_id = PasswordResetToken.verify_token(token)
    
    if not user_id:
        flash('Link inválido ou expirado. Solicite uma nova recuperação.', 'danger')
        return redirect(url_for('password.forgot_password'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user = User.query.get(user_id)
        user.set_password(form.password.data)
        
        # Marca o token como usado
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
        if reset_token:
            reset_token.mark_as_used()
        
        db.session.commit()
        
        flash('Senha alterada com sucesso! Faça login com sua nova senha.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)