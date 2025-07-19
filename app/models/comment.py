"""
Modelo de Comentario
Maneja los comentarios y observaciones en las tesis
"""

from datetime import datetime
from app import db

class Comment(db.Model):
    """Modelo de comentario del sistema"""
    
    __tablename__ = 'comments'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # Tipo de comentario
    comment_type = db.Column(db.Enum('general', 'revision', 'approval', 
                                    'rejection', 'suggestion', 'correction', 
                                    name='comment_types'), 
                            nullable=False, default='general')
    
    # Relaciones
    thesis_id = db.Column(db.Integer, db.ForeignKey('thesis.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))  # Para respuestas
    
    # Estado
    is_resolved = db.Column(db.Boolean, default=False)
    is_private = db.Column(db.Boolean, default=False)  # Solo visible para autor y destinatario
    
    # Metadatos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), 
                             lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, content, thesis_id, author_id, comment_type='general', **kwargs):
        """Inicializar comentario"""
        self.content = content
        self.thesis_id = thesis_id
        self.author_id = author_id
        self.comment_type = comment_type
        self.parent_id = kwargs.get('parent_id')
        self.is_private = kwargs.get('is_private', False)
    
    def get_comment_type_display(self):
        """Mostrar tipo de comentario en español"""
        types = {
            'general': 'Comentario General',
            'revision': 'Revisión',
            'approval': 'Aprobación',
            'rejection': 'Rechazo',
            'suggestion': 'Sugerencia',
            'correction': 'Corrección'
        }
        return types.get(self.comment_type, 'Desconocido')
    
    def get_comment_type_icon(self):
        """Obtener icono según el tipo de comentario"""
        icons = {
            'general': 'fas fa-comment',
            'revision': 'fas fa-eye',
            'approval': 'fas fa-check-circle text-success',
            'rejection': 'fas fa-times-circle text-danger',
            'suggestion': 'fas fa-lightbulb text-warning',
            'correction': 'fas fa-edit text-info'
        }
        return icons.get(self.comment_type, 'fas fa-comment')
    
    def get_comment_type_color(self):
        """Obtener color según el tipo de comentario"""
        colors = {
            'general': 'secondary',
            'revision': 'info',
            'approval': 'success',
            'rejection': 'danger',
            'suggestion': 'warning',
            'correction': 'primary'
        }
        return colors.get(self.comment_type, 'secondary')
    
    def is_reply(self):
        """Verificar si es una respuesta"""
        return self.parent_id is not None
    
    def can_be_viewed_by(self, user):
        """Verificar si el usuario puede ver el comentario"""
        if user.role == 'admin':
            return True
        
        # Si es privado, solo el autor y el estudiante de la tesis pueden verlo
        if self.is_private:
            return user.id in [self.author_id, self.thesis.student_id]
        
        # Si no es privado, todos los involucrados en la tesis pueden verlo
        return user.can_manage_thesis(self.thesis)
    
    def can_be_edited_by(self, user):
        """Verificar si el usuario puede editar el comentario"""
        # Solo el autor puede editar sus comentarios
        return user.id == self.author_id
    
    def can_be_replied_by(self, user):
        """Verificar si el usuario puede responder al comentario"""
        # Solo si puede ver el comentario y está involucrado en la tesis
        return self.can_be_viewed_by(user) and user.can_manage_thesis(self.thesis)
    
    def mark_as_resolved(self):
        """Marcar como resuelto"""
        self.is_resolved = True
        db.session.commit()
    
    def mark_as_unresolved(self):
        """Marcar como no resuelto"""
        self.is_resolved = False
        db.session.commit()
    
    def get_replies_count(self):
        """Obtener número de respuestas"""
        return self.replies.count()
    
    def get_thread_comments(self):
        """Obtener todos los comentarios del hilo"""
        if self.parent_id:
            # Si es una respuesta, obtener el comentario padre y sus respuestas
            parent = Comment.query.get(self.parent_id)
            return [parent] + list(parent.replies.order_by(Comment.created_at))
        else:
            # Si es un comentario padre, obtener él y sus respuestas
            return [self] + list(self.replies.order_by(Comment.created_at))
    
    def to_dict(self, include_replies=False):
        """Convertir a diccionario para API"""
        data = {
            'id': self.id,
            'content': self.content,
            'comment_type': self.comment_type,
            'comment_type_display': self.get_comment_type_display(),
            'comment_type_icon': self.get_comment_type_icon(),
            'comment_type_color': self.get_comment_type_color(),
            'thesis_id': self.thesis_id,
            'author_id': self.author_id,
            'parent_id': self.parent_id,
            'is_resolved': self.is_resolved,
            'is_private': self.is_private,
            'is_reply': self.is_reply(),
            'replies_count': self.get_replies_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_replies and not self.is_reply():
            data['replies'] = [reply.to_dict() for reply in self.replies.order_by(Comment.created_at)]
        
        return data
    
    def __repr__(self):
        return f'<Comment {self.id} by User {self.author_id} on Thesis {self.thesis_id}>'
