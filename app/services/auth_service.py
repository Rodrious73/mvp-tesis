"""
Servicio de autenticación
"""

import jwt
from datetime import datetime, timedelta
from flask import current_app
from app.models.user import User

class AuthService:
    """Servicio para manejar autenticación y JWT"""
    
    @staticmethod
    def authenticate_user(email, password):
        """Autenticar usuario con email y password"""
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.is_active:
            return None
        
        # Verificar si la cuenta está bloqueada
        if user.is_locked():
            return 'locked'
        
        if user.check_password(password):
            # Actualizar último login y resetear intentos fallidos
            user.update_last_login()
            return user
        else:
            # Incrementar intentos fallidos
            user.increment_failed_attempts()
            return None
    
    @staticmethod
    def generate_token(user):
        """Generar token JWT para el usuario"""
        payload = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24),  # Token válido por 24 horas
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return token
    
    @staticmethod
    def verify_token(token):
        """Verificar y decodificar token JWT"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Verificar que el usuario aún existe y está activo
            user = User.query.get(payload['user_id'])
            if not user or not user.is_active:
                return None
            
            return user
        
        except jwt.ExpiredSignatureError:
            return None  # Token expirado
        except jwt.InvalidTokenError:
            return None  # Token inválido
    
    @staticmethod
    def generate_reset_token(user):
        """Generar token para reset de password"""
        payload = {
            'user_id': user.id,
            'purpose': 'password_reset',
            'exp': datetime.utcnow() + timedelta(hours=1),  # Token válido por 1 hora
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return token
    
    @staticmethod
    def verify_reset_token(token):
        """Verificar token de reset de password"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Verificar que es un token de reset
            if payload.get('purpose') != 'password_reset':
                return None
            
            # Verificar que el usuario existe
            user = User.query.get(payload['user_id'])
            if not user:
                return None
            
            return user
        
        except jwt.ExpiredSignatureError:
            return None  # Token expirado
        except jwt.InvalidTokenError:
            return None  # Token inválido
    
    @staticmethod
    def check_role_permission(user, required_role):
        """Verificar si el usuario tiene el rol requerido"""
        role_hierarchy = {
            'admin': 3,
            'teacher': 2,
            'student': 1
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    @staticmethod
    def can_access_thesis(user, thesis):
        """Verificar si el usuario puede acceder a una tesis específica"""
        if user.role == 'admin':
            return True
        elif user.role == 'teacher':
            return user.id in [thesis.advisor_id, thesis.jury_id]
        elif user.role == 'student':
            return user.id == thesis.student_id
        
        return False
    
    @staticmethod
    def can_edit_thesis(user, thesis):
        """Verificar si el usuario puede editar una tesis"""
        if user.role == 'admin':
            return True
        elif user.role == 'student' and user.id == thesis.student_id:
            # El estudiante solo puede editar si está en estado borrador o requiere revisión
            return thesis.status in ['draft', 'revision_required']
        
        return False
    
    @staticmethod
    def can_review_thesis(user, thesis):
        """Verificar si el usuario puede revisar una tesis"""
        if user.role == 'admin':
            return True
        elif user.role == 'teacher':
            return user.id in [thesis.advisor_id, thesis.jury_id]
        
        return False
    
    @staticmethod
    def request_password_reset(email):
        """Solicitar reset de contraseña"""
        user = User.query.filter_by(email=email).first()
        if not user or not user.is_active:
            return None
        
        token = user.generate_password_reset_token()
        return user, token
    
    @staticmethod
    def reset_password_with_token(token, new_password):
        """Resetear contraseña usando token"""
        user = User.query.filter_by(password_reset_token=token).first()
        
        if not user or not user.verify_password_reset_token(token):
            return False
        
        user.reset_password(new_password)
        return True
    
    @staticmethod
    def unlock_user_account(user_id):
        """Desbloquear cuenta de usuario (solo admin)"""
        user = User.query.get(user_id)
        if user:
            user.reset_failed_attempts()
            return True
        return False
