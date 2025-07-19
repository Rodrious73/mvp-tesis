"""
Modelo de Notificación
Maneja las notificaciones del sistema
"""

from datetime import datetime
from app import db

class Notification(db.Model):
    """Modelo de notificación del sistema"""
    
    __tablename__ = 'notifications'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Tipo de notificación
    notification_type = db.Column(db.Enum('thesis_submitted', 'thesis_approved', 
                                         'thesis_rejected', 'thesis_revision_required',
                                         'new_comment', 'advisor_assigned', 
                                         'jury_assigned', 'defense_scheduled',
                                         'document_uploaded', 'status_change',
                                         'system_message',
                                         name='notification_types'), 
                                 nullable=False, default='system_message')
    
    # Relaciones
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    thesis_id = db.Column(db.Integer, db.ForeignKey('thesis.id'))  # Opcional
    
    # Estado
    is_read = db.Column(db.Boolean, default=False)
    
    # URL de acción (opcional)
    action_url = db.Column(db.String(500))  # URL a la que redirigir al hacer clic
    
    # Metadatos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    def __init__(self, title, message, user_id, notification_type='system_message', **kwargs):
        """Inicializar notificación"""
        self.title = title
        self.message = message
        self.user_id = user_id
        self.notification_type = notification_type
        self.thesis_id = kwargs.get('thesis_id')
        self.action_url = kwargs.get('action_url')
    
    def get_notification_type_display(self):
        """Mostrar tipo de notificación en español"""
        types = {
            'thesis_submitted': 'Tesis Presentada',
            'thesis_approved': 'Tesis Aprobada',
            'thesis_rejected': 'Tesis Rechazada',
            'thesis_revision_required': 'Revisión Requerida',
            'new_comment': 'Nuevo Comentario',
            'advisor_assigned': 'Asesor Asignado',
            'jury_assigned': 'Jurado Asignado',
            'defense_scheduled': 'Sustentación Programada',
            'document_uploaded': 'Documento Subido',
            'system_message': 'Mensaje del Sistema'
        }
        return types.get(self.notification_type, 'Notificación')
    
    def get_notification_icon(self):
        """Obtener icono según el tipo de notificación"""
        icons = {
            'thesis_submitted': 'fas fa-paper-plane text-info',
            'thesis_approved': 'fas fa-check-circle text-success',
            'thesis_rejected': 'fas fa-times-circle text-danger',
            'thesis_revision_required': 'fas fa-edit text-warning',
            'new_comment': 'fas fa-comment text-primary',
            'advisor_assigned': 'fas fa-user-plus text-info',
            'jury_assigned': 'fas fa-users text-info',
            'defense_scheduled': 'fas fa-calendar text-warning',
            'document_uploaded': 'fas fa-file-upload text-success',
            'system_message': 'fas fa-bell text-secondary'
        }
        return icons.get(self.notification_type, 'fas fa-bell')
    
    def get_notification_color(self):
        """Obtener color según el tipo de notificación"""
        colors = {
            'thesis_submitted': 'info',
            'thesis_approved': 'success',
            'thesis_rejected': 'danger',
            'thesis_revision_required': 'warning',
            'new_comment': 'primary',
            'advisor_assigned': 'info',
            'jury_assigned': 'info',
            'defense_scheduled': 'warning',
            'document_uploaded': 'success',
            'system_message': 'secondary'
        }
        return colors.get(self.notification_type, 'secondary')
    
    def mark_as_read(self):
        """Marcar como leída"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()
    
    def mark_as_unread(self):
        """Marcar como no leída"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            db.session.commit()
    
    def get_time_ago(self):
        """Obtener tiempo transcurrido desde la creación"""
        if not self.created_at:
            return "Fecha desconocida"
        
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"hace {diff.days} día{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"hace {hours} hora{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"hace {minutes} minuto{'s' if minutes > 1 else ''}"
        else:
            return "hace un momento"
    
    def to_dict(self):
        """Convertir a diccionario para API"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'notification_type_display': self.get_notification_type_display(),
            'notification_icon': self.get_notification_icon(),
            'notification_color': self.get_notification_color(),
            'user_id': self.user_id,
            'thesis_id': self.thesis_id,
            'is_read': self.is_read,
            'action_url': self.action_url,
            'time_ago': self.get_time_ago(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    @staticmethod
    def create_thesis_notification(notification_type, thesis, recipient_user, **kwargs):
        """Crear notificación relacionada con tesis"""
        # Mensajes predefinidos según el tipo
        messages = {
            'thesis_submitted': f'La tesis "{thesis.title}" ha sido presentada para revisión.',
            'thesis_approved': f'¡Felicitaciones! Tu tesis "{thesis.title}" ha sido aprobada.',
            'thesis_rejected': f'Tu tesis "{thesis.title}" ha sido rechazada. Revisa los comentarios.',
            'thesis_revision_required': f'Tu tesis "{thesis.title}" requiere revisiones. Revisa los comentarios.',
            'new_comment': f'Nuevo comentario en tu tesis "{thesis.title}".',
            'advisor_assigned': f'Has sido asignado como asesor de la tesis "{thesis.title}".',
            'jury_assigned': f'Has sido asignado como jurado de la tesis "{thesis.title}".',
            'document_uploaded': f'Nuevo documento subido en la tesis "{thesis.title}".'
        }
        
        title = kwargs.get('title', f'Actualización de Tesis - {thesis.title[:50]}...')
        message = kwargs.get('message', messages.get(notification_type, 'Actualización en tu tesis.'))
        action_url = kwargs.get('action_url', f'/thesis/{thesis.id}')
        
        notification = Notification(
            title=title,
            message=message,
            user_id=recipient_user.id,
            notification_type=notification_type,
            thesis_id=thesis.id,
            action_url=action_url
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title[:30]}... for User {self.user_id}>'
