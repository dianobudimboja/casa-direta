from flask import current_app
from flask_mail import Message
from ..extensions import mail

def send_reset_email(user, token):
    reset_url = f"{current_app.config['BASE_URL']}/password/reset/{token}"
    
    msg = Message(
        subject='Recuperação de Senha - Casa Direta',
        recipients=['diano.budimboja@gmail.com'],
        html=f"""
        <h2>Olá, {user.name}!</h2>
        <p>Clique no link para redefinir sua senha:</p>
        <a href="{reset_url}">{reset_url}</a>
        <p>Este link expira em 1 hora.</p>
        """
    )
    mail.send(msg)