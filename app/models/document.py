"""
Modelo de Documento
Maneja los archivos asociados a las tesis
"""

import os
from datetime import datetime
from app import db

class Document(db.Model):
    """Modelo de documento del sistema"""
    
    __tablename__ = 'documents'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Tamaño en bytes
    file_type = db.Column(db.String(50))  # Tipo MIME
    
    # Tipo de documento
    document_type = db.Column(db.Enum('proposal', 'chapter', 'full_thesis', 
                                     'presentation', 'appendix', 'other', 
                                     name='document_types'), 
                             nullable=False, default='other')
    
    # Relaciones
    thesis_id = db.Column(db.Integer, db.ForeignKey('thesis.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Metadatos
    description = db.Column(db.Text)
    version = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    
    # Fechas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con usuario que subió el archivo
    uploader = db.relationship('User', backref='uploaded_documents')
    
    def __init__(self, filename, original_filename, file_path, thesis_id, 
                 uploaded_by, document_type='other', **kwargs):
        """Inicializar documento"""
        self.filename = filename
        self.original_filename = original_filename
        self.file_path = file_path
        self.thesis_id = thesis_id
        self.uploaded_by = uploaded_by
        self.document_type = document_type
        self.description = kwargs.get('description')
        self.file_size = kwargs.get('file_size')
        self.file_type = kwargs.get('file_type')
    
    def get_document_type_display(self):
        """Mostrar tipo de documento en español"""
        types = {
            'proposal': 'Propuesta',
            'chapter': 'Capítulo',
            'full_thesis': 'Tesis Completa',
            'presentation': 'Presentación',
            'appendix': 'Anexo',
            'other': 'Otro'
        }
        return types.get(self.document_type, 'Desconocido')
    
    def get_type_display(self):
        """Alias para get_document_type_display() - para compatibilidad con templates"""
        return self.get_document_type_display()
    
    def get_file_extension(self):
        """Obtener extensión del archivo"""
        return os.path.splitext(self.original_filename)[1].lower()
    
    def get_file_size_formatted(self):
        """Obtener tamaño de archivo formateado"""
        if not self.file_size:
            return "Desconocido"
        
        # Convertir bytes a unidades más legibles
        file_size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if file_size < 1024.0:
                return f"{file_size:.1f} {unit}"
            file_size /= 1024.0
        return f"{file_size:.1f} TB"
    
    def get_file_size_display(self):
        """Alias para get_file_size_formatted() - para compatibilidad con templates"""
        return self.get_file_size_formatted()
    
    def get_icon_class(self):
        """Obtener clase de icono según el tipo de archivo"""
        extension = self.get_file_extension()
        icons = {
            '.pdf': 'fas fa-file-pdf text-danger',
            '.doc': 'fas fa-file-word text-primary',
            '.docx': 'fas fa-file-word text-primary',
            '.txt': 'fas fa-file-alt text-secondary',
            '.ppt': 'fas fa-file-powerpoint text-warning',
            '.pptx': 'fas fa-file-powerpoint text-warning',
            '.xls': 'fas fa-file-excel text-success',
            '.xlsx': 'fas fa-file-excel text-success',
            '.jpg': 'fas fa-file-image text-info',
            '.jpeg': 'fas fa-file-image text-info',
            '.png': 'fas fa-file-image text-info',
            '.gif': 'fas fa-file-image text-info'
        }
        return icons.get(extension, 'fas fa-file text-dark')
    
    def is_image(self):
        """Verificar si es una imagen"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return self.get_file_extension() in image_extensions
    
    def is_pdf(self):
        """Verificar si es un PDF"""
        return self.get_file_extension() == '.pdf'
    
    def can_be_viewed_online(self):
        """Verificar si se puede ver online"""
        viewable_extensions = ['.pdf', '.txt', '.jpg', '.jpeg', '.png', '.gif']
        return self.get_file_extension() in viewable_extensions
    
    def get_download_url(self):
        """Obtener URL de descarga"""
        return f"/download/{self.id}"
    
    def get_view_url(self):
        """Obtener URL de visualización"""
        if self.can_be_viewed_online():
            return f"/view/{self.id}"
        return None
    
    def delete_file(self):
        """Eliminar archivo físico del sistema"""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                return True
        except Exception as e:
            print(f"Error al eliminar archivo: {e}")
        return False
    
    def to_dict(self):
        """Convertir a diccionario para API"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'document_type': self.document_type,
            'document_type_display': self.get_document_type_display(),
            'file_size': self.file_size,
            'file_size_formatted': self.get_file_size_formatted(),
            'file_type': self.file_type,
            'file_extension': self.get_file_extension(),
            'icon_class': self.get_icon_class(),
            'description': self.description,
            'version': self.version,
            'is_active': self.is_active,
            'is_image': self.is_image(),
            'is_pdf': self.is_pdf(),
            'can_view_online': self.can_be_viewed_online(),
            'download_url': self.get_download_url(),
            'view_url': self.get_view_url(),
            'thesis_id': self.thesis_id,
            'uploaded_by': self.uploaded_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Document {self.original_filename} (Thesis {self.thesis_id})>'
