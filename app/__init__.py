from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS

from .config import Config
from .extensions import db, bcrypt, mail
from .utils.helpers import init_filters

# Login manager instance
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'


def create_app(config_class=Config):
    """Cria e configura a aplicação Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # Inicializa extensões
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    Migrate(app, db)

    # Registra blueprints (rotas)
    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    from .routes.dashboard import bp as dashboard_bp
    from .routes.chat import bp as chat_bp
    from .routes.admin import bp as admin_bp
    from .routes.verification import bp as verification_bp
    from .routes.reviews import bp as reviews_bp
    from .routes.password_reset import bp as password_bp
    from .routes.contracts import bp as contracts_bp
    from .routes.favorites import bp as favorites_bp
    from .routes.reports import bp as reports_bp
    from .routes.setup import bp as setup_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(verification_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(password_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(setup_bp)

    # API blueprints (futuro)
    # from .api.v1 import properties_api, ai_api
    # app.register_blueprint(properties_api.bp, url_prefix='/api/v1')
    # app.register_blueprint(ai_api.bp, url_prefix='/api/v1')

    # Registra filtros customizados para templates
    init_filters(app)

    # Importa modelos para o Alembic detectar
    from .models import user, property, message, review

    # Criar pastas de upload se não existirem
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'properties'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'users'), exist_ok=True)

    # ⭐ PÁGINAS DE ERRO PERSONALIZADAS ⭐
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app


@login_manager.user_loader
def load_user(user_id):
    """Carrega utilizador pelo ID para o Flask-Login."""
    from .models.user import User
    return User.query.get(int(user_id))