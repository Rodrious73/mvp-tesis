"""
Servicio de gestión de documentos
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from app import db
from app.models.document import Document
from app.services.notification_service import NotificationService

class DocumentService:
    """Servicio para gestionar documentos"""
    
    @staticmethod
    def allowed_file(filename):
        """Verificar si el archivo tiene una extensión permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    
    @staticmethod
    def generate_unique_filename(original_filename):
        """Generar nombre de archivo único"""
        # Obtener extensión
        ext = os.path.splitext(original_filename)[1]
        # Generar nombre único
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        return unique_filename
    
    @staticmethod
    def save_file(file, thesis_id, uploaded_by, document_type='other', description=None):
        """Guardar archivo en el sistema"""
        if not file or file.filename == '':
            raise ValueError("No se seleccionó ningún archivo")
        
        if not DocumentService.allowed_file(file.filename):
            raise ValueError("Tipo de archivo no permitido")
        
        # Generar nombre único
        original_filename = secure_filename(file.filename)
        unique_filename = DocumentService.generate_unique_filename(original_filename)
        
        # Crear directorio si no existe
        upload_folder = current_app.config['UPLOAD_FOLDER']
        thesis_folder = os.path.join(upload_folder, f"thesis_{thesis_id}")
        os.makedirs(thesis_folder, exist_ok=True)
        
        # Ruta completa del archivo
        file_path = os.path.join(thesis_folder, unique_filename)
        
        try:
            # Guardar archivo
            file.save(file_path)
            
            # Obtener información del archivo
            file_size = os.path.getsize(file_path)
            file_type = file.content_type
            
            # Crear registro en base de datos
            document = Document(
                filename=unique_filename,
                original_filename=original_filename,
                file_path=file_path,
                thesis_id=thesis_id,
                uploaded_by=uploaded_by,
                document_type=document_type,
                description=description,
                file_size=file_size,
                file_type=file_type
            )
            
            db.session.add(document)
            db.session.commit()
            
            # Crear notificación
            from app.models.thesis import Thesis
            thesis = Thesis.query.get(thesis_id)
            
            if thesis:
                # Notificar al asesor si existe
                if thesis.advisor_id and thesis.advisor_id != uploaded_by:
                    NotificationService.create_notification(
                        title="Nuevo documento subido",
                        message=f'Se subió un nuevo documento "{original_filename}" en la tesis "{thesis.title}".',
                        user_id=thesis.advisor_id,
                        notification_type='document_uploaded',
                        thesis_id=thesis_id
                    )
                
                # Notificar al jurado si existe
                if thesis.jury_id and thesis.jury_id != uploaded_by:
                    NotificationService.create_notification(
                        title="Nuevo documento subido",
                        message=f'Se subió un nuevo documento "{original_filename}" en la tesis "{thesis.title}".',
                        user_id=thesis.jury_id,
                        notification_type='document_uploaded',
                        thesis_id=thesis_id
                    )
            
            return document
            
        except Exception as e:
            # Si hay error, eliminar archivo si se creó
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
    
    @staticmethod
    def get_document_by_id(document_id):
        """Obtener documento por ID"""
        return Document.query.get(document_id)
    
    @staticmethod
    def download_document(document_id):
        """Descargar documento por ID"""
        from flask import send_file, abort
        
        document = Document.query.get(document_id)
        if not document or not document.is_active:
            abort(404, "Documento no encontrado")
        
        # Verificar que el archivo existe
        if not os.path.exists(document.file_path):
            abort(404, "Archivo no encontrado en el servidor")
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.original_filename,
            mimetype=document.file_type
        )
    
    @staticmethod
    def get_documents_by_thesis(thesis_id):
        """Obtener todos los documentos de una tesis"""
        return Document.query.filter_by(
            thesis_id=thesis_id, 
            is_active=True
        ).order_by(Document.created_at.desc()).all()
    
    @staticmethod
    def get_documents_by_type(thesis_id, document_type):
        """Obtener documentos por tipo"""
        return Document.query.filter_by(
            thesis_id=thesis_id, 
            document_type=document_type,
            is_active=True
        ).order_by(Document.created_at.desc()).all()
    
    @staticmethod
    def update_document(document_id, **kwargs):
        """Actualizar información del documento"""
        document = Document.query.get(document_id)
        if not document:
            raise ValueError("Documento no encontrado")
        
        # Campos que se pueden actualizar
        allowed_fields = ['description', 'document_type']
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(document, field):
                setattr(document, field, value)
        
        db.session.commit()
        return document
    
    @staticmethod
    def delete_document(document_id):
        """Eliminar documento (soft delete)"""
        document = Document.query.get(document_id)
        if not document:
            raise ValueError("Documento no encontrado")
        
        # Marcar como inactivo en lugar de eliminar
        document.is_active = False
        db.session.commit()
        
        return document
    
    @staticmethod
    def delete_document_permanently(document_id):
        """Eliminar documento permanentemente"""
        document = Document.query.get(document_id)
        if not document:
            raise ValueError("Documento no encontrado")
        
        # Eliminar archivo físico
        if document.delete_file():
            # Eliminar registro de base de datos
            db.session.delete(document)
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def get_file_path(document_id):
        """Obtener ruta del archivo"""
        document = Document.query.get(document_id)
        if document and document.is_active:
            return document.file_path
        return None
    
    @staticmethod
    def increment_version(document_id):
        """Incrementar versión del documento"""
        document = Document.query.get(document_id)
        if document:
            document.version += 1
            db.session.commit()
            return document
        return None
    
    @staticmethod
    def get_latest_version_by_type(thesis_id, document_type):
        """Obtener la última versión de un tipo de documento"""
        return Document.query.filter_by(
            thesis_id=thesis_id,
            document_type=document_type,
            is_active=True
        ).order_by(Document.version.desc()).first()
    
    @staticmethod
    def get_storage_statistics():
        """Obtener estadísticas de almacenamiento"""
        total_documents = Document.query.filter_by(is_active=True).count()
        total_size = db.session.query(
            db.func.sum(Document.file_size)
        ).filter_by(is_active=True).scalar() or 0
        
        # Estadísticas por tipo
        type_stats = db.session.query(
            Document.document_type,
            db.func.count(Document.id),
            db.func.sum(Document.file_size)
        ).filter_by(is_active=True).group_by(Document.document_type).all()
        
        return {
            'total_documents': total_documents,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_type': {
                doc_type: {
                    'count': count,
                    'size': size or 0,
                    'size_mb': round((size or 0) / (1024 * 1024), 2)
                }
                for doc_type, count, size in type_stats
            }
        }
    
    @staticmethod
    def clean_orphaned_files():
        """Limpiar archivos huérfanos (sin registro en BD)"""
        upload_folder = current_app.config['UPLOAD_FOLDER']
        cleaned_files = []
        
        if not os.path.exists(upload_folder):
            return cleaned_files
        
        # Obtener todos los archivos registrados en BD
        registered_files = {doc.file_path for doc in Document.query.all()}
        
        # Recorrer directorio de uploads
        for root, dirs, files in os.walk(upload_folder):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Si el archivo no está registrado, eliminarlo
                if file_path not in registered_files:
                    try:
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                    except Exception:
                        pass  # Ignorar errores de eliminación
        
        return cleaned_files
