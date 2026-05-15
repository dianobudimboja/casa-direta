from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from ..extensions import db
from ..models.user import User
from ..forms.verification_form import VerificationRequestForm, AdminVerificationForm
from ..utils.upload_helper import save_verification_file

bp = Blueprint('verification', __name__, url_prefix='/verify')


@bp.route('/request', methods=['GET', 'POST'])
@login_required
def request_verification():
    """Página para solicitar verificação de identidade."""
    
    # Se já está verificado
    if current_user.is_verified:
        flash('Você já é um utilizador verificado!', 'info')
        return redirect(url_for('dashboard.profile'))
    
    # Se já tem pedido pendente
    if current_user.verification_status == 'pending':
        flash('Você já tem um pedido de verificação pendente. Aguarde a análise.', 'warning')
        return redirect(url_for('dashboard.profile'))
    
    form = VerificationRequestForm()
    
    if form.validate_on_submit():
        # Salva os documentos
        bi_front = save_verification_file(form.bi_front.data, current_user.id, 'bi_front')
        bi_back = save_verification_file(form.bi_back.data, current_user.id, 'bi_back')
        
        property_doc = None
        if form.property_document.data:
            property_doc = save_verification_file(form.property_document.data, current_user.id, 'property_doc')
        
        # CORRIGIDO: SÓ AQUI define como pending!
        current_user.bi_front_photo = bi_front
        current_user.bi_back_photo = bi_back
        current_user.property_document = property_doc
        current_user.verification_status = 'pending'
        current_user.verification_requested_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Pedido de verificação enviado com sucesso! Nossa equipa irá analisar em até 48h.', 'success')
        return redirect(url_for('dashboard.profile'))
    
    return render_template('verification/request.html', form=form)


@bp.route('/status')
@login_required
def verification_status():
    """Verifica o status do pedido de verificação."""
    return render_template('verification/status.html')