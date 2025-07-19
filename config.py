import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-desarrollo-no-usar-en-produccion'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///thesis_system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-clave-desarrollo'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    
    # Configuraciones adicionales
    ITEMS_PER_PAGE = 10
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_thesis_system.db'

# Configuraciones disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
