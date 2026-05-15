from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user
from sqlalchemy import func
from datetime import datetime

from ..extensions import db
from ..models.property import Property
from ..models.message import Message
from ..models.review import Review
from ..forms.role_form import RoleRequestForm
from ..services.notification_service import notify_role_request_processed

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@bp.route('/')
@login_required
def index():
    """Dashboard principal do utilizador."""
    
    # Calcular estatísticas do utilizador
    total_views = db.session.query(func.sum(Property.views)).filter_by(user_id=current_user.id).scalar() or 0
    total_inquiries = db.session.query(func.sum(Property.inquiries)).filter_by(user_id=current_user.id).scalar() or 0
    active_properties = Property.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    # Calcular preço médio dos imóveis do utilizador (apenas para senhorios)
    avg_price = 0
    if current_user.is_landlord:
        avg_price_result = db.session.query(func.avg(Property.price)).filter_by(user_id=current_user.id).scalar()
        avg_price = float(avg_price_result) if avg_price_result else 0
    
    # Estatísticas do utilizador
    stats = {
        'properties_count': current_user.properties_count,
        'active_properties': active_properties,
        'total_views': total_views,
        'total_inquiries': total_inquiries,
        'unread_messages': current_user.unread_messages_count(),
        'rating': current_user.rating,
        'successful_deals': current_user.successful_deals,
        'avg_price': avg_price,  # ← ADICIONADO
        'total_reviews': current_user.total_reviews  # ← ADICIONADO
    }
    
    # Últimos imóveis publicados
    recent_properties = Property.query.filter_by(user_id=current_user.id).order_by(Property.created_at.desc()).limit(5).all()
    
    # Últimas mensagens
    recent_messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.created_at.desc()).limit(10).all()
    
    return render_template(
        'dashboard/index.html',
        stats=stats,
        recent_properties=recent_properties,
        recent_messages=recent_messages
    )


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Página de perfil do utilizador."""
    if request.method == 'POST':
        # Atualizar perfil
        current_user.name = request.form.get('name', current_user.name)
        current_user.phone = request.form.get('phone', current_user.phone)
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard.profile'))
    
    return render_template('dashboard/profile.html', user=current_user)


@bp.route('/properties')
@login_required
def my_properties():
    """Lista de imóveis do utilizador."""
    page = request.args.get('page', 1, type=int)
    properties = Property.query.filter_by(user_id=current_user.id).order_by(
        Property.created_at.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('dashboard/properties.html', properties=properties)


@bp.route('/property/<int:property_id>/toggle-status')
@login_required
def toggle_property_status(property_id):
    """Ativa/desativa um imóvel."""
    property_obj = Property.query.get_or_404(property_id)
    
    if property_obj.user_id != current_user.id and not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    property_obj.is_active = not property_obj.is_active
    db.session.commit()
    
    status = 'ativado' if property_obj.is_active else 'desativado'
    flash(f'Imóvel {status} com sucesso!', 'success')
    return redirect(url_for('dashboard.my_properties'))


@bp.route('/property/<int:property_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    """Editar um imóvel existente."""
    property_obj = Property.query.get_or_404(property_id)
    
    if property_obj.user_id != current_user.id and not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard.my_properties'))
    
    from ..forms.property_form import PropertyForm
    form = PropertyForm()
    
    if form.validate_on_submit():
        # Processa novas fotos
        if form.photos.data:
            uploaded_photos = property_obj.photos or []
            for photo in form.photos.data:
                if photo and photo.filename:
                    filename = save_uploaded_file(photo, 'properties')
                    if filename:
                        uploaded_photos.append(filename)
                        if not property_obj.main_photo:
                            property_obj.main_photo = filename
            
            property_obj.photos = uploaded_photos
        
        # Atualiza outros campos
        property_obj.title = form.title.data
        property_obj.description = form.description.data
        property_obj.price = form.price.data
        property_obj.location = form.location.data
        property_obj.address = form.address.data
        property_obj.neighborhood = form.neighborhood.data
        property_obj.bedrooms = form.bedrooms.data
        property_obj.bathrooms = form.bathrooms.data
        property_obj.area = form.area.data
        property_obj.is_featured = form.is_featured.data
        
        db.session.commit()
        flash('Imóvel atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard.my_properties'))
    
    elif request.method == 'GET':
        form.title.data = property_obj.title
        form.description.data = property_obj.description
        form.price.data = property_obj.price
        form.location.data = property_obj.location
        form.address.data = property_obj.address
        form.neighborhood.data = property_obj.neighborhood
        form.bedrooms.data = property_obj.bedrooms
        form.bathrooms.data = property_obj.bathrooms
        form.area.data = property_obj.area
        form.is_featured.data = property_obj.is_featured
    
    property_obj.latitude = form.latitude.data
    property_obj.longitude = form.longitude.data
    
    return render_template('properties/edit.html', form=form, property=property_obj)

@bp.route('/property/<int:property_id>/delete')
@login_required
def delete_property(property_id):
    """Remove um imóvel."""
    property_obj = Property.query.get_or_404(property_id)
    
    if property_obj.user_id != current_user.id and not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    db.session.delete(property_obj)
    current_user.properties_count -= 1
    db.session.commit()
    
    flash('Imóvel removido com sucesso!', 'success')
    return redirect(url_for('dashboard.my_properties'))

@bp.route('/property/<int:property_id>/delete-photo/<path:photo>')
@login_required
def delete_photo(property_id, photo):
    """Remove uma foto específica do imóvel."""
    
    property_obj = Property.query.get_or_404(property_id)
    
    # Verificar se o utilizador é o dono
    if property_obj.user_id != current_user.id and not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard.my_properties'))
    
    # Remover o ficheiro do disco
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'properties', photo)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Remover da lista de fotos
    if property_obj.photos and photo in property_obj.photos:
        property_obj.photos.remove(photo)
        
        # Se a foto removida era a principal, atualizar
        if property_obj.main_photo == photo:
            property_obj.main_photo = property_obj.photos[0] if property_obj.photos else None
        
        db.session.commit()
        flash('Foto removida com sucesso!', 'success')
    else:
        flash('Foto não encontrada.', 'warning')
    
    return redirect(url_for('dashboard.edit_property', property_id=property_id))



@bp.route('/request-landlord', methods=['GET', 'POST'])
@login_required
def request_landlord():
    """Página para inquilino solicitar tornar-se senhorio."""
    
    # Verificar se já é senhorio
    if current_user.is_landlord:
        flash('Você já é senhorio na plataforma.', 'info')
        return redirect(url_for('dashboard.profile'))
    
    # Verificar se já tem pedido pendente
    if current_user.requested_role == 'landlord':
        flash('Você já tem um pedido pendente para se tornar senhorio. Aguarde a análise.', 'warning')
        return redirect(url_for('dashboard.profile'))
    
    form = RoleRequestForm()
    
    if form.validate_on_submit():
        current_user.requested_role = 'landlord'
        current_user.role_request_date = datetime.utcnow()
        current_user.role_request_notes = form.notes.data
        db.session.commit()
        
        flash('Pedido enviado com sucesso! A nossa equipa irá analisar e entrará em contacto.', 'success')
        return redirect(url_for('dashboard.profile'))
    
    return render_template('dashboard/request_landlord.html', form=form)



@bp.route('/cancel-request')
@login_required
def cancel_landlord_request():
    """Cancela o pedido de tornar-se senhorio."""
    
    if current_user.requested_role == 'landlord':
        current_user.requested_role = None
        current_user.role_request_date = None
        current_user.role_request_notes = None
        db.session.commit()
        flash('Pedido cancelado com sucesso.', 'info')
    
    return redirect(url_for('dashboard.profile'))


@bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    """Página para eliminar a própria conta."""
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Verificar senha
        if not current_user.check_password(password):
            flash('Palavra-passe incorreta. Não foi possível eliminar a conta.', 'danger')
            return redirect(url_for('dashboard.delete_account'))
        
        # Guardar dados para mensagem (antes de eliminar)
        user_name = current_user.name
        user_email = current_user.email
        
        # Eliminar conta (os relacionamentos em cascata fazem o resto)
        db.session.delete(current_user)
        db.session.commit()
        
        # Fazer logout
        logout_user()
        
        flash(f'✅ Conta "{user_name}" ({user_email}) foi eliminada permanentemente.', 'info')
        return redirect(url_for('main.index'))
    
    return render_template('dashboard/delete_account.html')