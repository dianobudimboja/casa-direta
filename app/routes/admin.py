from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime

from ..extensions import db
from ..models.user import User
from ..models.property import Property
from ..models.review import Review
from ..services.notification_service import notify_verification_result
from ..models.report import Report
from ..services.notification_service import notify_role_request_processed

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator para verificar se o utilizador é admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso negado. Área administrativa.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Dashboard administrativo."""
    # Estatísticas
    stats = {
        'total_users': User.query.count(),
        'total_properties': Property.query.count(),
        'pending_verifications': User.query.filter_by(verification_status='pending').count(),
        'suspicious_properties': Property.query.filter(Property.requires_review == True).count(),
        'reported_properties': 0,
        'total_reviews': Review.query.count(),
        'pending_reports': Report.query.filter_by(status='pending').count(),
        'pending_role_requests': User.query.filter_by(requested_role='landlord').count()
    }
    
    # Últimos utilizadores registados
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Imóveis suspeitos
    suspicious_properties = Property.query.filter_by(requires_review=True).limit(10).all()
    
    # Pedidos de verificação pendentes
    pending_verifications = User.query.filter_by(verification_status='pending').limit(10).all()
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_users=recent_users,
        suspicious_properties=suspicious_properties,
        pending_verifications=pending_verifications
    )


@bp.route('/users')
@login_required
@admin_required
def users():
    """Lista de utilizadores."""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')
    
    query = User.query
    
    if filter_type == 'pending':
        query = query.filter_by(verification_status='pending')
    elif filter_type == 'verified':
        query = query.filter_by(is_verified=True)
    elif filter_type == 'landlords':
        query = query.filter_by(is_landlord=True)
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html', users=users, current_filter=filter_type)


@bp.route('/properties')
@login_required
@admin_required
def properties():
    """Lista de imóveis para moderação."""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')
    
    query = Property.query
    
    if filter_type == 'suspicious':
        query = query.filter_by(requires_review=True)
    elif filter_type == 'unverified':
        query = query.filter_by(is_verified=False)
    elif filter_type == 'pending':
        query = query.filter(Property.is_verified == False, Property.requires_review == False)
    
    properties_list = query.order_by(Property.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template(
        'admin/properties.html', 
        properties=properties_list, 
        current_filter=filter_type
    )


@bp.route('/property/<int:property_id>/verify')
@login_required
@admin_required
def verify_property(property_id):
    """Verifica um imóvel (remove suspeita)."""
    property_obj = Property.query.get_or_404(property_id)
    property_obj.is_verified = True
    property_obj.requires_review = False
    property_obj.suspicion_score = 0
    db.session.commit()
    
    flash(f'Imóvel "{property_obj.title}" verificado com sucesso!', 'success')
    return redirect(url_for('admin.properties'))


@bp.route('/property/<int:property_id>/delete')
@login_required
@admin_required
def delete_property(property_id):
    """Remove um imóvel fraudulento."""
    property_obj = Property.query.get_or_404(property_id)
    title = property_obj.title
    
    user = property_obj.owner
    if user:
        user.properties_count -= 1
    
    db.session.delete(property_obj)
    db.session.commit()
    
    flash(f'Imóvel "{title}" removido permanentemente.', 'warning')
    return redirect(url_for('admin.properties'))


@bp.route('/user/<int:user_id>/verify')
@login_required
@admin_required
def verify_user(user_id):
    """Verifica a identidade de um utilizador."""
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    user.verification_status = 'approved'
    user.verification_processed_at = datetime.utcnow()
    user.verified_by = current_user.id
    db.session.commit()
    
    flash(f'Utilizador {user.name} verificado com sucesso!', 'success')
    return redirect(url_for('admin.users'))

# ⭐ NOVAS ROTAS PARA VERIFICAÇÃO DE DOCUMENTOS ⭐

@bp.route('/verifications')
@login_required
@admin_required
def verifications():
    """Lista de pedidos de verificação pendentes."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    
    query = User.query.filter(User.verification_status == status)
    
    # Contagens para cada status (passar para o template)
    pending_count = User.query.filter_by(verification_status='pending').count()
    approved_count = User.query.filter_by(verification_status='approved').count()
    rejected_count = User.query.filter_by(verification_status='rejected').count()
    
    users = query.order_by(User.verification_requested_at.asc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template(
        'admin/verifications.html', 
        users=users, 
        current_status=status,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count
    )


@bp.route('/verification/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def review_verification(user_id):
    """Revisão de um pedido de verificação específico."""
    user = User.query.get_or_404(user_id)
    
    from ..forms.verification_form import AdminVerificationForm
    form = AdminVerificationForm()
    
    if form.validate_on_submit():
        if form.action.data == 'approve':
            user.is_verified = True
            user.verification_status = 'approved'
            flash(f'Utilizador {user.name} foi verificado com sucesso!', 'success')
        else:
            user.is_verified = False
            user.verification_status = 'rejected'
            user.verification_rejection_reason = form.rejection_reason.data
            flash(f'Verificação de {user.name} foi rejeitada.', 'warning')
        
        user.verification_processed_at = datetime.utcnow()
        user.verified_by = current_user.id
        db.session.commit()

        notify_verification_result(user, is_approved=(form.action.data == 'approve'), 
            rejection_reason=form.rejection_reason.data if form.action.data == 'reject' else None)
        
        return redirect(url_for('admin.verifications'))
    
    return render_template('admin/review_verification.html', user=user, form=form)


@bp.route('/verification/<int:user_id>/view-doc/<doc_type>')
@login_required
@admin_required
def view_document(user_id, doc_type):
    """Visualiza um documento de verificação."""
    user = User.query.get_or_404(user_id)
    
    doc_map = {
        'bi_front': user.bi_front_photo,
        'bi_back': user.bi_back_photo,
        'property': user.property_document
    }
    
    filename = doc_map.get(doc_type)
    if not filename:
        flash('Documento não encontrado.', 'danger')
        return redirect(url_for('admin.review_verification', user_id=user_id))
    
    return redirect(url_for('static', filename=f'uploads/verifications/{filename}'))


@bp.route('/reviews')
@login_required
@admin_required
def reviews():
    """Lista de avaliações para moderação."""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')
    
    query = Review.query
    
    if filter_type == 'reported':
        # Avaliações reportadas (implementar depois)
        pass
    
    reviews_list = query.order_by(Review.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/reviews.html', reviews=reviews_list, current_filter=filter_type)

@bp.route('/user/<int:user_id>/suspend')
@login_required
@admin_required
def suspend_user(user_id):
    """Suspende ou ativa um utilizador."""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Não pode suspender outro administrador.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Alternar status
    user.is_active = not user.is_active
    status = 'suspenso' if not user.is_active else 'ativado'
    db.session.commit()
    
    flash(f'Utilizador {user.name} foi {status}.', 'warning')
    return redirect(url_for('admin.users'))


@bp.route('/role-requests')
@login_required
@admin_required
def role_requests():
    """Lista de pedidos de mudança de papel."""
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    
    if status == 'pending':
        query = User.query.filter_by(requested_role='landlord')
    elif status == 'approved':
        query = User.query.filter_by(is_landlord=True).filter(User.requested_role.is_(None))
    else:
        query = User.query
    
    users = query.order_by(User.role_request_date.desc()).paginate(page=page, per_page=20, error_out=False)
    
    pending_count = User.query.filter_by(requested_role='landlord').count()
    
    return render_template('admin/role_requests.html', 
                          users=users, 
                          current_status=status,
                          pending_count=pending_count)


@bp.route('/role-request/<int:user_id>/approve')
@login_required
@admin_required
def approve_role_request(user_id):
    """Aprova o pedido de um inquilino para se tornar senhorio."""
    
    user = User.query.get_or_404(user_id)
    
    if user.requested_role != 'landlord':
        flash('Este utilizador não tem um pedido pendente.', 'warning')
        return redirect(url_for('admin.role_requests'))
    
    # Tornar senhorio
    user.is_landlord = True
    user.requested_role = None
    user.role_request_processed_at = datetime.utcnow()
    user.role_request_processed_by = current_user.id
    
    db.session.commit()
    
    # Enviar notificação por email
    notify_role_request_processed(user, approved=True)
    
    flash(f'✅ {user.name} agora é senhorio. Uma notificação foi enviada por email.', 'success')
    return redirect(url_for('admin.role_requests'))


@bp.route('/role-request/<int:user_id>/reject')
@login_required
@admin_required
def reject_role_request(user_id):
    """Rejeita o pedido de um inquilino para se tornar senhorio."""
    
    user = User.query.get_or_404(user_id)
    
    if user.requested_role != 'landlord':
        flash('Este utilizador não tem um pedido pendente.', 'warning')
        return redirect(url_for('admin.role_requests'))
    
    user.requested_role = None
    user.role_request_date = None
    user.role_request_notes = None
    user.role_request_processed_at = datetime.utcnow()
    user.role_request_processed_by = current_user.id
    
    db.session.commit()
    
    # Enviar notificação por email
    notify_role_request_processed(user, approved=False)
    
    flash(f'❌ Pedido de {user.name} foi rejeitado. Uma notificação foi enviada por email.', 'warning')
    return redirect(url_for('admin.role_requests'))


@bp.route('/user/<int:user_id>/demote')
@login_required
@admin_required
def demote_user(user_id):
    """Rebaixa um senhorio a inquilino (apenas se não tiver imóveis ativos)."""
    
    user = User.query.get_or_404(user_id)
    
    if not user.is_landlord:
        flash('Este utilizador já é inquilino.', 'info')
        return redirect(url_for('admin.users'))
    
    # Verificar se tem imóveis ativos
    active_properties = Property.query.filter_by(user_id=user.id, is_active=True).count()
    
    if active_properties > 0:
        flash(f'Não pode rebaixar {user.name} pois tem {active_properties} imóvel(is) ativo(s).', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_landlord = False
    db.session.commit()
    
    flash(f'✅ {user.name} foi rebaixado para inquilino.', 'warning')
    return redirect(url_for('admin.users'))


@bp.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def admin_delete_user(user_id):
    """Elimina um utilizador pelo administrador."""
    
    user = User.query.get_or_404(user_id)
    
    # Não permitir eliminar a si mesmo (admin)
    if user.id == current_user.id:
        flash('Não pode eliminar a sua própria conta através do painel admin.', 'danger')
        return redirect(url_for('admin.users'))
    
    user_name = user.name
    user_email = user.email
    
    # Eliminar utilizador (cascata apaga tudo)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'✅ Utilizador "{user_name}" ({user_email}) foi eliminado permanentemente.', 'success')
    return redirect(url_for('admin.users'))