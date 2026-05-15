import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuração base."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Database - Já suporta PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///casa_direta.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = 86400  # 24 horas
    
    # Upload (⚠️ Atenção: Vercel não suporta escrita em disco)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_PHOTOS_PER_PROPERTY = 10
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    
    # URL Base (apenas uma vez!)
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # Pagination
    PROPERTIES_PER_PAGE = 12
    
    # Anti-intermediary limits
    MAX_PROPERTIES_UNVERIFIED = 1
    MAX_PROPERTIES_VERIFIED = 10
    MAX_MESSAGES_PER_MINUTE = 10


class DevelopmentConfig(Config):
    """Configuração de desenvolvimento."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuração de produção."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    """Configuração de testes."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False