from flask import current_app, render_template
from flask_mail import Message
from threading import Thread
from ..extensions import mail


def send_async_email(app, msg):
    """Envia email em background (não bloqueia a requisição)."""
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, html_body, text_body=None):
    """Envia email de forma assíncrona."""
    msg = Message(subject, recipients=recipients)
    msg.html = html_body
    if text_body:
        msg.body = text_body
    
    # Envia em background
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()


def notify_new_message(receiver, sender, property_title):
    """Notifica quando recebe uma nova mensagem."""
    subject = f"📩 Nova mensagem de {sender.name} - Casa Direta"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #3b82f6, #8b5cf6); padding: 20px; text-align: center; color: white;">
            <h1 style="margin: 0;">🏠 Casa Direta</h1>
        </div>
        <div style="padding: 20px;">
            <h2>Olá, {receiver.name}!</h2>
            <p>Você recebeu uma nova mensagem de <strong>{sender.name}</strong> sobre o imóvel <strong>{property_title}</strong>.</p>
            <p>Responda diretamente pelo chat da plataforma.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{current_app.config['BASE_URL']}/chat" style="background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">
                    Ver mensagem
                </a>
            </div>
        </div>
        <div style="background: #f1f5f9; padding: 10px; text-align: center; font-size: 12px; color: #64748b;">
            Casa Direta - Arrendar diretamente com segurança
        </div>
    </body>
    </html>
    """
    
    send_email(subject, [receiver.email], html)


def notify_contract_generated(contract, landlord, tenant_email, tenant_name):
    """Notifica as partes sobre um novo contrato gerado."""
    
    # Email para o senhorio
    landlord_html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #3b82f6, #8b5cf6); padding: 20px; text-align: center; color: white;">
            <h1 style="margin: 0;">📄 Contrato Gerado</h1>
        </div>
        <div style="padding: 20px;">
            <h2>Olá, {landlord.name}!</h2>
            <p>O contrato de arrendamento para o imóvel <strong>{contract.property_title}</strong> foi gerado com sucesso.</p>
            <p><strong>Inquilino:</strong> {contract.tenant_name}</p>
            <p><strong>Período:</strong> {contract.start_date.strftime('%d/%m/%Y')} a {contract.end_date.strftime('%d/%m/%Y')}</p>
            <p><strong>Valor mensal:</strong> {contract.property_rent:,.0f} Kz</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{current_app.config['BASE_URL']}/contracts/{contract.id}" style="background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">
                    Ver contrato
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    
    send_email("📄 Contrato de arrendamento gerado", [landlord.email], landlord_html)
    
    # Se o inquilino tiver email, enviar também
    if tenant_email:
        tenant_html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #3b82f6, #8b5cf6); padding: 20px; text-align: center; color: white;">
                <h1 style="margin: 0;">📄 Contrato de Arrendamento</h1>
            </div>
            <div style="padding: 20px;">
                <h2>Olá, {tenant_name}!</h2>
                <p>O senhorio <strong>{landlord.name}</strong> gerou o contrato para o imóvel <strong>{contract.property_title}</strong>.</p>
                <p>Solicite o documento ao senhorio ou faça login na plataforma.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{current_app.config['BASE_URL']}/register" style="background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">
                        Criar conta
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        send_email("📄 Contrato de arrendamento gerado para si", [tenant_email], tenant_html)


def notify_verification_result(user, is_approved, rejection_reason=None):
    """Notifica o resultado da verificação de identidade."""
    
    if is_approved:
        subject = "✅ Verificação aprovada - Casa Direta"
        html = f"""
        <div style="background: #10b981; padding: 20px; text-align: center; color: white;">
            <h1>✅ Verificação Aprovada!</h1>
        </div>
        <div style="padding: 20px;">
            <h2>Parabéns, {user.name}!</h2>
            <p>Sua identidade foi verificada com sucesso. Agora você tem o selo de confiança da Casa Direta.</p>
            <p><strong>Benefícios:</strong></p>
            <ul>
                <li>Publicar até 10 imóveis</li>
                <li>Maior confiança dos inquilinos</li>
                <li>Anúncios com prioridade</li>
            </ul>
        </div>
        """
    else:
        subject = "❌ Verificação rejeitada - Casa Direta"
        html = f"""
        <div style="background: #ef4444; padding: 20px; text-align: center; color: white;">
            <h1>❌ Verificação Rejeitada</h1>
        </div>
        <div style="padding: 20px;">
            <h2>Olá, {user.name}</h2>
            <p>Infelizmente sua solicitação de verificação foi rejeitada.</p>
            <p><strong>Motivo:</strong> {rejection_reason or 'Documentos inválidos ou ilegíveis'}</p>
            <p>Por favor, envie novos documentos legíveis e tente novamente.</p>
            <div style="text-align: center; margin: 20px 0;">
                <a href="{current_app.config['BASE_URL']}/verify/request" style="background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Solicitar novamente
                </a>
            </div>
        </div>
        """
    
    send_email(subject, [user.email], html)


def send_async_email(app, msg):
    """Envia email em background (não bloqueia a requisição)."""
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, html_body, text_body=None):
    """Envia email de forma assíncrona."""
    msg = Message(subject, recipients=recipients)
    msg.html = html_body
    if text_body:
        msg.body = text_body
    
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()


def notify_role_request_processed(user, approved):
    """Notifica o utilizador sobre o resultado do pedido de senhorio."""
    
    if approved:
        subject = "✅ Pedido de Senhorio Aprovado - Casa Direta"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 20px; text-align: center; color: white;">
                <h1 style="margin: 0;">✅ Pedido Aprovado!</h1>
            </div>
            <div style="padding: 20px;">
                <h2>Parabéns, {user.name}!</h2>
                <p>O seu pedido para se tornar <strong>senhorio</strong> foi <strong style="color: #10b981;">APROVADO</strong>.</p>
                <p>Agora pode publicar imóveis na plataforma Casa Direta.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{current_app.config['BASE_URL']}/create" style="background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">
                        Publicar Imóvel
                    </a>
                </div>
                <p>Se tiver dúvidas, contacte o nosso suporte.</p>
                <hr style="margin: 20px 0;">
                <p style="color: #64748b; font-size: 12px;">Casa Direta - Arrendar diretamente com segurança</p>
            </div>
        </body>
        </html>
        """
    else:
        subject = "❌ Pedido de Senhorio Rejeitado - Casa Direta"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #ef4444, #dc2626); padding: 20px; text-align: center; color: white;">
                <h1 style="margin: 0;">❌ Pedido Rejeitado</h1>
            </div>
            <div style="padding: 20px;">
                <h2>Olá, {user.name}</h2>
                <p>O seu pedido para se tornar <strong>senhorio</strong> foi <strong style="color: #ef4444;">REJEITADO</strong>.</p>
                <p>Motivos possíveis:</p>
                <ul>
                    <li>Documentação insuficiente</li>
                    <li>Informações inconsistentes</li>
                    <li>Histórico de atividade suspeita</li>
                </ul>
                <p>Entre em contacto com o suporte para mais informações.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{current_app.config['BASE_URL']}/contact" style="background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">
                        Contactar Suporte
                    </a>
                </div>
                <hr style="margin: 20px 0;">
                <p style="color: #64748b; font-size: 12px;">Casa Direta - Arrendar diretamente com segurança</p>
            </div>
        </body>
        </html>
        """
    
    send_email(subject, [user.email], html_body)