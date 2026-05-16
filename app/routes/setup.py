from flask import Blueprint, jsonify
from ..extensions import db
from ..models import User, Property, Message, Review, Contract, Favorite, Report

bp = Blueprint('setup', __name__, url_prefix='/setup')

@bp.route('/create-tables')
def create_tables():
    """Rota temporária para criar todas as tabelas."""
    try:
        db.create_all()
        return jsonify({'status': 'success', 'message': 'Tabelas criadas com sucesso!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/create-admin')
def create_admin():
    """Rota temporária para criar administrador."""
    try:
        from ..models.user import User
        admin = User.query.filter_by(email='diano.budimboja@gmail.com').first()
        if admin:
            admin.is_admin = True
            admin.is_verified = True
        else:
            admin = User(
                name='Administrador',
                email='diano.budimboja@gmail.com',
                is_admin=True,
                is_verified=True
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Admin criado/atualizado!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500