from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from ..extensions import db
from ..models.user import User
from ..forms.auth_form import LoginForm, RegistrationForm

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login (aceita email ou telefone)."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        import re
        email_or_phone = form.email_or_phone.data.strip()
        user = None
        
        # Verificar se é email (contém @)
        if '@' in email_or_phone:
            user = User.query.filter_by(email=email_or_phone).first()
        else:
            # Tentar encontrar por telefone (normalizando)
            phone_clean = re.sub(r'[\s\+\(\)\-]', '', email_or_phone)
            # Extrair últimos 9 dígitos
            if len(phone_clean) >= 9:
                phone_normalized = phone_clean[-9:]
                user = User.query.filter_by(phone=phone_normalized).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('A sua conta está suspensa. Contacte o suporte.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Bem-vindo de volta, {user.name}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('Email/Telefone ou palavra-passe inválidos.', 'danger')
    
    return render_template('auth/login.html', form=form)
    

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registo de novo utilizador."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # CORRIGIDO: NÃO define verification_status - o default 'none' será usado
        user = User(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            is_landlord=(form.user_type.data == 'landlord')
            # verification_status fica 'none' automaticamente
            # is_verified fica False automaticamente
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        flash(f'Conta criada com sucesso! Bem-vindo à Casa Direta, {user.name}!', 'success')
        
        if user.is_landlord:
            flash('Complete o seu perfil e comece a publicar os seus imóveis!', 'info')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Comece a explorar os imóveis disponíveis!', 'info')
            return redirect(url_for('main.index'))
    
    return render_template('auth/register.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """Faz logout do utilizador."""
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/verify/<int:user_id>')
@login_required
def verify_user(user_id):
    """Rota para verificar identidade (apenas admin)."""
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    user.verification_status = 'approved'
    db.session.commit()
    
    flash(f'Utilizador {user.name} verificado com sucesso!', 'success')
    return redirect(url_for('admin.dashboard'))