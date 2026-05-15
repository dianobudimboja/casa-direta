from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import os

from ..extensions import db
from ..models.contract import Contract
from ..models.property import Property
from ..models.user import User
from ..forms.contract_form import ContractForm
from ..services.pdf_service import generate_rental_contract
from ..services.notification_service import notify_contract_generated

bp = Blueprint('contracts', __name__, url_prefix='/contracts')



@bp.route('/create/<int:property_id>', methods=['GET', 'POST'])
@login_required
def create_contract(property_id):
    """Criar um novo contrato para um imóvel."""
    
    property_obj = Property.query.get_or_404(property_id)
    
    # Verificar se o utilizador é o proprietário
    if property_obj.user_id != current_user.id:
        flash('Apenas o proprietário do imóvel pode criar contratos.', 'danger')
        return redirect(url_for('main.property_detail', property_id=property_id))
    
    form = ContractForm()
    
    if form.validate_on_submit():
        # Calcular duração em meses
        duration_months = (form.end_date.data.year - form.start_date.data.year) * 12 + (form.end_date.data.month - form.start_date.data.month)
        
        # Dados para o PDF
        contract_data = {
            'property_id': property_id,
            'property_title': property_obj.title,
            'property_address': property_obj.address or property_obj.location,
            'property_rent': property_obj.price,
            'landlord_name': current_user.name,
            'tenant_name': form.tenant_name.data.strip(),
            'tenant_bi': form.tenant_bi.data or '',
            'tenant_phone': form.tenant_phone.data or '',
            'start_date': form.start_date.data,
            'end_date': form.end_date.data,
            'duration_months': duration_months,
            'payment_day': form.payment_day.data,
            'security_deposit': form.security_deposit.data or 0,
            'additional_clauses': form.additional_clauses.data or ''
        }
        
        # Gerar PDF
        pdf_filename = None  # ← INICIALIZAR A VARIÁVEL AQUI!
        
        try:
            pdf_filename = generate_rental_contract(contract_data)
            print(f"✅ PDF gerado: {pdf_filename}")
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
            return render_template('contracts/create.html', form=form, property=property_obj)
        
        # Verificar se o PDF foi gerado
        if not pdf_filename:
            flash('Erro ao gerar o PDF. Tente novamente.', 'danger')
            return render_template('contracts/create.html', form=form, property=property_obj)
        
        # Salvar contrato na base de dados
        contract = Contract(
            property_id=property_id,
            property_title=property_obj.title,
            property_address=property_obj.address or property_obj.location,
            property_rent=property_obj.price,
            landlord_id=current_user.id,
            landlord_name=current_user.name,
            landlord_phone=current_user.phone,
            tenant_name=form.tenant_name.data.strip(),
            tenant_bi=form.tenant_bi.data,
            tenant_phone=form.tenant_phone.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            payment_day=form.payment_day.data,
            security_deposit=form.security_deposit.data or 0,
            additional_clauses=form.additional_clauses.data,
            status='draft',
            pdf_path=pdf_filename
        )
        
        db.session.add(contract)
        db.session.commit()

        tenant_email = None
        tenant_name = form.tenant_name.data

        # Se o inquilino já tiver conta, usar email dela
        tenant_user = User.query.filter_by(name=tenant_name).first()
        if tenant_user:
            tenant_email = tenant_user.email

        notify_contract_generated(contract, current_user, tenant_email, tenant_name)
        
        flash(f'✅ Contrato gerado com sucesso!', 'success')
        return redirect(url_for('contracts.view_contract', contract_id=contract.id))
    
    return render_template('contracts/create.html', form=form, property=property_obj)


@bp.route('/<int:contract_id>')
@login_required
def view_contract(contract_id):
    """Visualizar detalhes do contrato."""
    
    contract = Contract.query.get_or_404(contract_id)
    
    # Verificar permissão
    if contract.landlord_id != current_user.id and contract.tenant_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('contracts/view.html', contract=contract)


@bp.route('/<int:contract_id>/download')
@login_required
def download_contract(contract_id):
    """Fazer download do PDF do contrato."""
    
    contract = Contract.query.get_or_404(contract_id)
    
    # Verificar permissão
    if contract.landlord_id != current_user.id and contract.tenant_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    from flask import current_app
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'contracts', contract.pdf_path)
    
    if not os.path.exists(filepath):
        flash('Ficheiro do contrato não encontrado.', 'danger')
        return redirect(url_for('contracts.view_contract', contract_id=contract_id))
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"contrato_{contract.property_title}.pdf",
        mimetype='application/pdf'
    )


@bp.route('/my-contracts')
@login_required
def my_contracts():
    """Lista de contratos do utilizador."""
    
    contracts = Contract.query.filter(
        (Contract.landlord_id == current_user.id) | (Contract.tenant_id == current_user.id)
    ).order_by(Contract.created_at.desc()).all()
    
    return render_template('contracts/my_contracts.html', contracts=contracts)