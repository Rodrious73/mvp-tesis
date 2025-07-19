"""
Servicio de gestión de usuarios
"""

from app import db
from app.models.user import User

class UserService:
    """Servicio para gestionar usuarios"""
    
    @staticmethod
    def create_user(email, password, first_name, last_name, role='student', **kwargs):
        """Crear un nuevo usuario"""
        # Verificar si el email ya existe
        if User.query.filter_by(email=email).first():
            raise ValueError("El email ya está registrado")
        
        # Crear usuario
        user = User(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            **kwargs
        )
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def get_user_by_id(user_id):
        """Obtener usuario por ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_email(email):
        """Obtener usuario por email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_users_by_role(role):
        """Obtener usuarios por rol"""
        return User.query.filter_by(role=role, is_active=True).all()
    
    @staticmethod
    def get_active_users():
        """Obtener todos los usuarios activos"""
        return User.query.filter_by(is_active=True).all()
    
    @staticmethod
    def update_user(user_id, **kwargs):
        """Actualizar información del usuario"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        # Campos que se pueden actualizar
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'student_code', 
            'career', 'department', 'specialization'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        db.session.commit()
        return user
    
    @staticmethod
    def change_password(user_id, new_password):
        """Cambiar contraseña del usuario"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        user.set_password(new_password)
        db.session.commit()
        return user
    
    @staticmethod
    def activate_user(user_id):
        """Activar usuario"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        user.is_active = True
        db.session.commit()
        return user
    
    @staticmethod
    def deactivate_user(user_id):
        """Desactivar usuario"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        user.is_active = False
        db.session.commit()
        return user
    
    @staticmethod
    def get_teachers():
        """Obtener lista de docentes activos"""
        return User.query.filter_by(role='teacher', is_active=True).all()
    
    @staticmethod
    def get_students():
        """Obtener lista de estudiantes activos"""
        return User.query.filter_by(role='student', is_active=True).all()
    
    @staticmethod
    def search_users(query, role=None):
        """Buscar usuarios por nombre, email o código"""
        search = f"%{query}%"
        users_query = User.query.filter(
            db.or_(
                User.first_name.ilike(search),
                User.last_name.ilike(search),
                User.email.ilike(search),
                User.student_code.ilike(search)
            )
        )
        
        if role:
            users_query = users_query.filter_by(role=role)
        
        return users_query.filter_by(is_active=True).all()

def create_default_users():
    """Crear usuarios por defecto para el sistema"""
    
    # Verificar si ya existen usuarios
    if User.query.count() > 0:
        return
    
    # Crear administrador por defecto
    admin = User(
        email='admin@unjfsc.edu.pe',
        password='admin123',
        first_name='Administrador',
        last_name='Sistema',
        role='admin'
    )
    
    # Crear docente por defecto
    teacher = User(
        email='docente@unjfsc.edu.pe',
        password='docente123',
        first_name='Dr. Juan',
        last_name='Pérez García',
        role='teacher',
        department='Ingeniería de Sistemas',
        specialization='Inteligencia Artificial y Machine Learning'
    )
    
    # Crear estudiante por defecto
    student = User(
        email='estudiante@unjfsc.edu.pe',
        password='estudiante123',
        first_name='María',
        last_name='González López',
        role='student',
        student_code='2020100001',
        career='Ingeniería de Sistemas'
    )
    
    # Crear otro docente
    teacher2 = User(
        email='docente2@unjfsc.edu.pe',
        password='docente123',
        first_name='Dra. Ana',
        last_name='Martínez Silva',
        role='teacher',
        department='Ingeniería Industrial',
        specialization='Gestión de Proyectos y Calidad'
    )
    
    # Crear otro estudiante
    student2 = User(
        email='estudiante2@unjfsc.edu.pe',
        password='estudiante123',
        first_name='Carlos',
        last_name='Rodríguez Mendoza',
        role='student',
        student_code='2020100002',
        career='Ingeniería Industrial'
    )
    
    try:
        db.session.add_all([admin, teacher, student, teacher2, student2])
        db.session.commit()
        print("✅ Usuarios por defecto creados exitosamente")
        print("👤 Admin: admin@unjfsc.edu.pe / admin123")
        print("👨‍🏫 Docente: docente@unjfsc.edu.pe / docente123")
        print("🎓 Estudiante: estudiante@unjfsc.edu.pe / estudiante123")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al crear usuarios por defecto: {e}")

def get_teachers():
    """Obtener todos los docentes activos"""
    return User.query.filter_by(role='teacher', is_active=True).all()

def search_users(query, role=None):
    """Buscar usuarios por nombre o email"""
    search = f"%{query}%"
    user_query = User.query.filter(
        db.or_(
            User.first_name.ilike(search),
            User.last_name.ilike(search),
            User.email.ilike(search)
        ),
        User.is_active == True
    )
    
    if role:
        user_query = user_query.filter_by(role=role)
    
    return user_query.all()
