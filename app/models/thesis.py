"""
Modelo de Tesis
Maneja la información de las tesis y su estado
"""

from datetime import datetime
from app import db

class Thesis(db.Model):
    """Modelo de tesis del sistema"""
    
    __tablename__ = 'thesis'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    
    # Estado de la tesis
    status = db.Column(db.Enum('draft', 'submitted', 'under_review', 'approved', 
                              'rejected', 'revision_required', 'completed', 
                              name='thesis_status'), 
                      nullable=False, default='draft')
    
    # Relaciones con usuarios
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    advisor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    jury_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Información académica
    career = db.Column(db.String(100), nullable=False)
    research_line = db.Column(db.String(200))  # Línea de investigación
    keywords = db.Column(db.String(500))  # Palabras clave separadas por comas
    
    # Fechas importantes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)  # Fecha de presentación
    defense_date = db.Column(db.DateTime)  # Fecha de sustentación
    
    # Calificaciones
    grade = db.Column(db.Float)  # Nota final
    grade_letter = db.Column(db.String(2))  # Nota en letras (A, B, C, etc.)
    
    # Metadatos
    is_public = db.Column(db.Boolean, default=False)  # Si es visible públicamente
    views_count = db.Column(db.Integer, default=0)  # Número de visualizaciones
    
    # Relaciones
    documents = db.relationship('Document', backref='thesis', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='thesis', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, title, student_id, career, description=None, **kwargs):
        """Inicializar tesis"""
        self.title = title
        self.student_id = student_id
        self.career = career
        self.description = description
        self.research_line = kwargs.get('research_line')
        self.keywords = kwargs.get('keywords')
    
    def get_status_display(self):
        """Mostrar estado en español"""
        status_dict = {
            'draft': 'Borrador',
            'submitted': 'Presentada',
            'under_review': 'En Revisión',
            'approved': 'Aprobada',
            'rejected': 'Rechazada',
            'revision_required': 'Requiere Revisión',
            'completed': 'Completada'
        }
        return status_dict.get(self.status, 'Estado Desconocido')
    
    def get_status_color(self):
        """Obtener color para el estado"""
        colors = {
            'draft': 'secondary',
            'submitted': 'info',
            'under_review': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'revision_required': 'warning',
            'completed': 'primary'
        }
        return colors.get(self.status, 'secondary')
    
    def get_status_icon(self):
        """Obtener icono para el estado"""
        icons = {
            'draft': 'edit',
            'submitted': 'paper-plane',
            'under_review': 'eye',
            'approved': 'check-circle',
            'rejected': 'times-circle',
            'revision_required': 'exclamation-triangle',
            'completed': 'trophy'
        }
        return icons.get(self.status, 'question-circle')
    
    def can_be_edited_by(self, user):
        """Verificar si el usuario puede editar la tesis"""
        if user.role == 'admin':
            return True
        elif user.role == 'student' and user.id == self.student_id:
            return self.status in ['draft', 'revision_required']
        return False
    
    def can_be_reviewed_by(self, user):
        """Verificar si el usuario puede revisar la tesis"""
        if user.role == 'admin':
            return True
        elif user.role == 'teacher':
            return user.id in [self.advisor_id, self.jury_id]
        return False
    
    def submit_for_review(self):
        """Presentar tesis para revisión"""
        if self.status == 'draft':
            self.status = 'submitted'
            self.submitted_at = datetime.utcnow()
            return True
        return False
    
    def approve(self, grade=None):
        """Aprobar tesis"""
        if self.status in ['submitted', 'under_review', 'revision_required']:
            self.status = 'approved'
            if grade:
                self.grade = grade
            return True
        return False
    
    def reject(self):
        """Rechazar tesis"""
        if self.status in ['submitted', 'under_review', 'revision_required']:
            self.status = 'rejected'
            return True
        return False
    
    def require_revision(self):
        """Requerir revisión"""
        if self.status in ['submitted', 'under_review']:
            self.status = 'revision_required'
            return True
        return False
    
    def start_review(self):
        """Iniciar revisión"""
        if self.status == 'submitted':
            self.status = 'under_review'
            return True
        return False
    
    def complete(self):
        """Marcar como completada"""
        if self.status == 'approved':
            self.status = 'completed'
            return True
        return False
    
    def get_keywords_list(self):
        """Obtener keywords como lista"""
        if self.keywords:
            return [kw.strip() for kw in self.keywords.split(',')]
        return []
    
    def get_progress_percentage(self):
        """Obtener porcentaje de progreso"""
        progress_map = {
            'draft': 10,
            'submitted': 30,
            'under_review': 60,
            'revision_required': 45,
            'approved': 90,
            'completed': 100,
            'rejected': 0
        }
        return progress_map.get(self.status, 0)
    
    def increment_views(self):
        """Incrementar contador de vistas"""
        self.views_count += 1
        db.session.commit()
    
    def to_dict(self):
        """Convertir a diccionario para API"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'status_display': self.get_status_display(),
            'status_color': self.get_status_color(),
            'student_id': self.student_id,
            'advisor_id': self.advisor_id,
            'jury_id': self.jury_id,
            'career': self.career,
            'research_line': self.research_line,
            'keywords': self.get_keywords_list(),
            'grade': self.grade,
            'grade_letter': self.grade_letter,
            'is_public': self.is_public,
            'views_count': self.views_count,
            'progress_percentage': self.get_progress_percentage(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'defense_date': self.defense_date.isoformat() if self.defense_date else None
        }
    
    def __repr__(self):
        return f'<Thesis {self.title[:50]}... ({self.status})>'
