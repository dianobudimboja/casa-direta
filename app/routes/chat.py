from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

from ..extensions import db
from ..models.message import Message
from ..models.property import Property
from ..models.user import User
from ..services.notification_service import notify_new_message

bp = Blueprint('chat', __name__, url_prefix='/chat')


@bp.route('/')
@login_required
def inbox():
    """Caixa de entrada de mensagens."""
    # Conversas únicas (agrupadas por utilizador e imóvel)
    conversations = db.session.query(
        Message.property_id,
        Message.sender_id,
        Message.receiver_id,
        db.func.max(Message.created_at).label('last_message'),
        db.func.count(Message.id).label('count')
    ).filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).group_by(
        Message.property_id,
        Message.sender_id,
        Message.receiver_id
    ).order_by(db.desc('last_message')).all()
    
    # Processar conversas para exibição
    conversation_list = []
    for conv in conversations:
        other_user_id = conv.sender_id if conv.sender_id != current_user.id else conv.receiver_id
        other_user = User.query.get(other_user_id)
        property_obj = Property.query.get(conv.property_id)
        
        # Contar não lidas nesta conversa
        unread = Message.query.filter_by(
            receiver_id=current_user.id,
            sender_id=other_user_id,
            property_id=conv.property_id,
            read=False
        ).count()
        
        conversation_list.append({
            'other_user': other_user,
            'property': property_obj,
            'last_message_date': conv.last_message,
            'unread_count': unread
        })
    
    return render_template('dashboard/messages.html', conversations=conversation_list)


@bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Envia uma mensagem (AJAX ou formulário)."""
    property_id = request.form.get('property_id')
    receiver_id = request.form.get('receiver_id')
    content = request.form.get('content')
    
    if not content or not content.strip():
        flash('Mensagem não pode estar vazia.', 'warning')
        return redirect(request.referrer or url_for('main.index'))
    
    # Verificar limites (anti-spam)
    recent_messages = Message.query.filter(
        Message.sender_id == current_user.id,
        Message.created_at > datetime.utcnow()
    ).count()
    
    max_per_minute = 10  # Configurável
    if recent_messages >= max_per_minute:
        flash('Você enviou muitas mensagens. Aguarde um momento.', 'danger')
        return redirect(request.referrer or url_for('main.index'))
    
    message = Message(
        content=content.strip(),
        sender_id=current_user.id,
        receiver_id=int(receiver_id),
        property_id=int(property_id)
    )
    
    db.session.add(message)
    
    # Incrementa contador de mensagens do imóvel
    property_obj = Property.query.get(property_id)
    if property_obj:
        property_obj.increment_inquiries()
    
    db.session.commit()
    
    if property_obj and property_obj.user_id != current_user.id:
    # Notificar o proprietário sobre nova mensagem
        notify_new_message(property_obj.owner, current_user, property_obj.title)

    # Resposta AJAX se for requisição JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': {
                'content': message.content,
                'created_at': message.created_at.strftime('%H:%M'),
                'sender_name': current_user.name
            }
        })
    
    flash('Mensagem enviada com sucesso!', 'success')
    return redirect(request.referrer or url_for('main.index'))


@bp.route('/conversation/<int:other_user_id>/<int:property_id>')
@login_required
def conversation(other_user_id, property_id):
    """Visualiza uma conversa específica."""
    other_user = User.query.get_or_404(other_user_id)
    property_obj = Property.query.get_or_404(property_id)
    
    # Busca mensagens entre os dois utilizadores sobre este imóvel
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user.id)),
        Message.property_id == property_id
    ).order_by(Message.created_at.asc()).all()
    
    # Marca mensagens como lidas
    for message in messages:
        if message.receiver_id == current_user.id and not message.read:
            message.read = True
    db.session.commit()
    
    return render_template(
        'chat/conversation.html',
        other_user=other_user,
        property=property_obj,
        messages=messages
    )


@bp.route('/mark-read/<int:message_id>')
@login_required
def mark_read(message_id):
    """Marca uma mensagem como lida (AJAX)."""
    message = Message.query.get_or_404(message_id)
    
    if message.receiver_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    message.mark_as_read()
    return jsonify({'success': True})


@bp.route('/unread-count')
@login_required
def unread_count():
    """Retorna número de mensagens não lidas (AJAX)."""
    count = current_user.unread_messages_count()
    return jsonify({'unread_count': count})