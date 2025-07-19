"""
Sistema de Gestión de Tesis Digital - UNJFSC
Inicialización de la aplicación Flask
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config

# Instancias de extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name='default'):
    """Factory pattern para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    # Registrar blueprints
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.routes.student import student as student_blueprint
    app.register_blueprint(student_blueprint, url_prefix='/student')
    
    from app.routes.teacher import teacher as teacher_blueprint
    app.register_blueprint(teacher_blueprint, url_prefix='/teacher')
    
    from app.routes.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    # Función para cargar usuario
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Agregar filtros de template personalizados
    from datetime import datetime
    
    @app.template_filter('moment')
    def moment_filter(date):
        """Filtro personalizado para formatear fechas"""
        if not date:
            return ''
        if isinstance(date, str):
            try:
                date = datetime.fromisoformat(date)
            except ValueError:
                return date
        return date
    
    @app.template_filter('format_date')
    def format_date(date, format='%d/%m/%Y %H:%M'):
        """Filtro para formatear fechas"""
        if not date:
            return ''
        if isinstance(date, str):
            try:
                date = datetime.fromisoformat(date)
            except ValueError:
                return date
        return date.strftime(format)
    
    @app.template_filter('from_now')
    def from_now(date):
        """Filtro para mostrar tiempo relativo"""
        if not date:
            return ''
        if isinstance(date, str):
            try:
                date = datetime.fromisoformat(date)
            except ValueError:
                return date
        
        now = datetime.now()
        diff = now - date
        
        if diff.days > 0:
            return f'hace {diff.days} días'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'hace {hours} horas'
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f'hace {minutes} minutos'
        else:
            return 'hace unos momentos'
    
    # Crear tablas en el contexto de la aplicación
    with app.app_context():
        db.create_all()
        
        # Crear usuarios por defecto si no existen
        from app.services.user_service import create_default_users
        create_default_users()
    
    return app
