from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

from ..extensions import db
from ..models.report import Report
from ..models.property import Property
from ..models.user import User
from ..forms.report_form import ReportForm

bp = Blueprint('reports', __name__, url_prefix='/reports')


@bp.route('/create/<int:property_id>', methods=['GET', 'POST'])
@login_required
def create_report(property_id):
    """Criar uma denúncia para um imóvel."""
    
    property_obj = Property.query.get_or_404(property_id)
    
    # Não pode denunciar o próprio imóvel
    if property_obj.user_id == current_user.id:
        flash('Não pode denunciar o seu próprio anúncio.', 'warning')
        return redirect(url_for('main.property_detail', property_id=property_id))
    
    # Verificar se já denunciou este imóvel
    existing_report = Report.query.filter_by(
        reporter_id=current_user.id,
        property_id=property_id,
        status='pending'
    ).first()
    
    if existing_report:
        flash('Você já denunciou este anúncio. A nossa equipa irá analisar.', 'warning')
        return redirect(url_for('main.property_detail', property_id=property_id))
    
    form = ReportForm()
    
    if form.validate_on_submit():
        report = Report(
            reason=form.reason.data,
            description=form.description.data,
            reporter_id=current_user.id,
            property_id=property_id
        )
        
        db.session.add(report)
        db.session.commit()
        
        flash('Denúncia enviada com sucesso! A nossa equipa irá analisar o anúncio.', 'success')
        return redirect(url_for('main.property_detail', property_id=property_id))
    
    return render_template('reports/create.html', form=form, property=property_obj)


@bp.route('/admin')
@login_required
def admin_reports():
    """Painel de denúncias para administrador."""
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    status = request.args.get('status', 'pending')
    page = request.args.get('page', 1, type=int)
    
    query = Report.query.filter_by(status=status)
    reports = query.order_by(Report.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    # Contagens para o dashboard
    pending_count = Report.query.filter_by(status='pending').count() or 0
    approved_count = Report.query.filter_by(status='approved').count() or 0
    rejected_count = Report.query.filter_by(status='rejected').count() or 0
    
    return render_template('admin/reports.html', 
                          reports=reports, 
                          current_status=status,
                          pending_count=pending_count,
                          approved_count=approved_count,
                          rejected_count=rejected_count)


@bp.route('/<int:report_id>/process', methods=['POST'])
@login_required
def process_report(report_id):
    """Processar uma denúncia (admin)."""
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    report = Report.query.get_or_404(report_id)
    action = request.form.get('action')
    admin_notes = request.form.get('admin_notes', '')
    
    if action == 'approve':
        # Remover o imóvel
        property_obj = report.property
        if property_obj:
            title = property_obj.title
            db.session.delete(property_obj)
            flash(f'Imóvel "{title}" removido devido à denúncia confirmada.', 'warning')
        
        report.status = 'approved'
        
    elif action == 'reject':
        report.status = 'rejected'
        flash('Denúncia rejeitada. O imóvel permanece ativo.', 'info')
    
    else:
        flash('Ação inválida.', 'danger')
        return redirect(url_for('reports.admin_reports'))
    
    report.processed_at = datetime.utcnow()
    report.processed_by = current_user.id
    report.admin_notes = admin_notes
    db.session.commit()
    
    return redirect(url_for('reports.admin_reports'))