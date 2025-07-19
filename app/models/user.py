"""
Modelo de Usuario
Maneja la autenticación y roles de usuarios
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """Modelo de usuario del sistema"""
    
    __tablename__ = 'users'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Información personal
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15))
    
    # Rol y estado
    role = db.Column(db.Enum('student', 'teacher', 'admin', name='user_roles'), 
                     nullable=False, default='student')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Información específica para estudiantes
    student_code = db.Column(db.String(20), unique=True)  # Código de estudiante
    career = db.Column(db.String(100))  # Carrera
    
    # Información específica para docentes
    department = db.Column(db.String(100))  # Departamento académico
    specialization = db.Column(db.String(200))  # Especialización
    
    # Metadatos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Seguridad - Bloqueo por intentos fallidos
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    password_reset_token = db.Column(db.String(100))
    password_reset_expires = db.Column(db.DateTime)
    
    # Relaciones
    thesis_as_student = db.relationship('Thesis', foreign_keys='Thesis.student_id', 
                                       backref='student', lazy='dynamic')
    thesis_as_advisor = db.relationship('Thesis', foreign_keys='Thesis.advisor_id', 
                                       backref='advisor', lazy='dynamic')
    thesis_as_jury = db.relationship('Thesis', foreign_keys='Thesis.jury_id', 
                                    backref='jury', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    def __init__(self, email, password, first_name, last_name, role='student', **kwargs):
        """Inicializar usuario"""
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        
        # Asignar campos específicos según el rol
        if role == 'student':
            self.student_code = kwargs.get('student_code')
            self.career = kwargs.get('career')
        elif role == 'teacher':
            self.department = kwargs.get('department')
            self.specialization = kwargs.get('specialization')
    
    def set_password(self, password):
        """Establecer password encriptado"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar password"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        """Obtener nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}"
    
    def get_role_display(self):
        """Mostrar rol en español"""
        roles = {
            'student': 'Estudiante',
            'teacher': 'Docente',
            'admin': 'Administrador'
        }
        return roles.get(self.role, 'Desconocido')
    
    def can_manage_thesis(self, thesis):
        """Verificar si el usuario puede gestionar una tesis"""
        if self.role == 'admin':
            return True
        elif self.role == 'teacher':
            return self.id in [thesis.advisor_id, thesis.jury_id]
        elif self.role == 'student':
            return self.id == thesis.student_id
        return False
    
    def get_unread_notifications_count(self):
        """Obtener número de notificaciones no leídas"""
        return self.notifications.filter_by(is_read=False).count()
    
    def update_last_login(self):
        """Actualizar último login"""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0  # Resetear intentos fallidos
        self.locked_until = None  # Quitar bloqueo si existía
        db.session.commit()
    
    def is_locked(self):
        """Verificar si la cuenta está bloqueada"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def increment_failed_attempts(self):
        """Incrementar intentos fallidos de login"""
        self.failed_login_attempts += 1
        
        # Bloquear cuenta después de 5 intentos fallidos por 30 minutos
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        db.session.commit()
    
    def reset_failed_attempts(self):
        """Resetear intentos fallidos"""
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    def generate_password_reset_token(self):
        """Generar token para reset de contraseña"""
        import secrets
        from datetime import timedelta
        
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)  # Válido por 1 hora
        db.session.commit()
        return self.password_reset_token
    
    def verify_password_reset_token(self, token):
        """Verificar token de reset de contraseña"""
        if (self.password_reset_token == token and 
            self.password_reset_expires and 
            self.password_reset_expires > datetime.utcnow()):
            return True
        return False
    
    def reset_password(self, new_password):
        """Resetear contraseña usando token"""
        self.set_password(new_password)
        self.password_reset_token = None
        self.password_reset_expires = None
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    def to_dict(self):
        """Convertir a diccionario para API"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'role_display': self.get_role_display(),
            'is_active': self.is_active,
            'student_code': self.student_code,
            'career': self.career,
            'department': self.department,
            'specialization': self.specialization,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
