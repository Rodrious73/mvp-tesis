"""
Servicio de gestión de tesis
"""

from datetime import datetime
from app import db
from app.models.thesis import Thesis
from app.models.user import User
from app.services.notification_service import NotificationService

class ThesisService:
    """Servicio para gestionar tesis"""
    
    @staticmethod
    def create_thesis(title, student_id, career, description=None, **kwargs):
        """Crear una nueva tesis"""
        # Verificar que el estudiante existe
        student = User.query.get(student_id)
        if not student or student.role != 'student':
            raise ValueError("Estudiante no válido")
        
        # Verificar que el estudiante no tenga una tesis activa
        existing_thesis = Thesis.query.filter_by(student_id=student_id).filter(
            Thesis.status.in_(['draft', 'submitted', 'under_review', 'revision_required'])
        ).first()
        
        if existing_thesis:
            raise ValueError("El estudiante ya tiene una tesis en proceso")
        
        # Crear tesis
        thesis = Thesis(
            title=title,
            student_id=student_id,
            career=career,
            description=description,
            **kwargs
        )
        
        db.session.add(thesis)
        db.session.commit()
        
        return thesis
    
    @staticmethod
    def get_thesis_by_id(thesis_id):
        """Obtener tesis por ID"""
        return Thesis.query.get(thesis_id)
    
    @staticmethod
    def get_thesis_by_student(student_id):
        """Obtener tesis de un estudiante"""
        return Thesis.query.filter_by(student_id=student_id).all()
    
    @staticmethod
    def get_thesis_by_advisor(advisor_id):
        """Obtener tesis donde el usuario es asesor"""
        return Thesis.query.filter_by(advisor_id=advisor_id).all()
    
    @staticmethod
    def get_thesis_by_jury(jury_id):
        """Obtener tesis donde el usuario es jurado"""
        return Thesis.query.filter_by(jury_id=jury_id).all()
    
    @staticmethod
    def get_thesis_by_status(status):
        """Obtener tesis por estado"""
        return Thesis.query.filter_by(status=status).all()
    
    @staticmethod
    def update_thesis(thesis_id, **kwargs):
        """Actualizar información de la tesis"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        # Campos que se pueden actualizar
        allowed_fields = [
            'title', 'description', 'research_line', 'keywords', 'career'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(thesis, field):
                setattr(thesis, field, value)
        
        db.session.commit()
        return thesis
    
    @staticmethod
    def submit_thesis(thesis_id):
        """Presentar tesis para revisión"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        if thesis.submit_for_review():
            db.session.commit()
            
            # Crear notificaciones
            if thesis.advisor_id:
                NotificationService.create_notification(
                    title="Nueva tesis para revisar",
                    message=f'La tesis "{thesis.title}" ha sido presentada para revisión.',
                    user_id=thesis.advisor_id,
                    notification_type='thesis_submitted',
                    thesis_id=thesis.id
                )
            
            return thesis
        
        raise ValueError("No se puede presentar la tesis en su estado actual")
    
    @staticmethod
    def start_review(thesis_id, reviewer_id):
        """Iniciar revisión de tesis"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        # Verificar que el revisor puede revisar esta tesis
        reviewer = User.query.get(reviewer_id)
        if not reviewer or reviewer.role not in ['teacher', 'admin']:
            raise ValueError("Revisor no válido")
        
        if thesis.start_review():
            db.session.commit()
            
            # Notificar al estudiante
            NotificationService.create_notification(
                title="Revisión iniciada",
                message=f'La revisión de tu tesis "{thesis.title}" ha comenzado.',
                user_id=thesis.student_id,
                notification_type='thesis_submitted',
                thesis_id=thesis.id
            )
            
            return thesis
        
        raise ValueError("No se puede iniciar la revisión en el estado actual")
    
    @staticmethod
    def approve_thesis(thesis_id, reviewer_id, grade=None):
        """Aprobar tesis"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        if thesis.approve(grade):
            db.session.commit()
            
            # Notificar al estudiante
            NotificationService.create_notification(
                title="¡Tesis Aprobada!",
                message=f'¡Felicitaciones! Tu tesis "{thesis.title}" ha sido aprobada.',
                user_id=thesis.student_id,
                notification_type='thesis_approved',
                thesis_id=thesis.id
            )
            
            return thesis
        
        raise ValueError("No se puede aprobar la tesis en su estado actual")
    
    @staticmethod
    def reject_thesis(thesis_id, reviewer_id):
        """Rechazar tesis"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        if thesis.reject():
            db.session.commit()
            
            # Notificar al estudiante
            NotificationService.create_notification(
                title="Tesis Rechazada",
                message=f'Tu tesis "{thesis.title}" ha sido rechazada. Revisa los comentarios para más detalles.',
                user_id=thesis.student_id,
                notification_type='thesis_rejected',
                thesis_id=thesis.id
            )
            
            return thesis
        
        raise ValueError("No se puede rechazar la tesis en su estado actual")
    
    @staticmethod
    def require_revision(thesis_id, reviewer_id):
        """Requerir revisión de la tesis"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        if thesis.require_revision():
            db.session.commit()
            
            # Notificar al estudiante
            NotificationService.create_notification(
                title="Revisión Requerida",
                message=f'Tu tesis "{thesis.title}" requiere revisiones. Revisa los comentarios.',
                user_id=thesis.student_id,
                notification_type='thesis_revision_required',
                thesis_id=thesis.id
            )
            
            return thesis
        
        raise ValueError("No se puede requerir revisión en el estado actual")
    
    @staticmethod
    def assign_advisor(thesis_id, advisor_id):
        """Asignar asesor a la tesis"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        advisor = User.query.get(advisor_id)
        if not advisor or advisor.role != 'teacher':
            raise ValueError("Asesor no válido")
        
        thesis.advisor_id = advisor_id
        db.session.commit()
        
        # Notificar al asesor
        NotificationService.create_notification(
            title="Nuevo Asesoramiento",
            message=f'Has sido asignado como asesor de la tesis "{thesis.title}".',
            user_id=advisor_id,
            notification_type='advisor_assigned',
            thesis_id=thesis.id
        )
        
        # Notificar al estudiante
        NotificationService.create_notification(
            title="Asesor Asignado",
            message=f'Se ha asignado un asesor a tu tesis "{thesis.title}".',
            user_id=thesis.student_id,
            notification_type='advisor_assigned',
            thesis_id=thesis.id
        )
        
        return thesis
    
    @staticmethod
    def assign_jury(thesis_id, jury_id):
        """Asignar jurado a la tesis"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        jury = User.query.get(jury_id)
        if not jury or jury.role != 'teacher':
            raise ValueError("Jurado no válido")
        
        thesis.jury_id = jury_id
        db.session.commit()
        
        # Notificar al jurado
        NotificationService.create_notification(
            title="Nuevo Jurado Asignado",
            message=f'Has sido asignado como jurado de la tesis "{thesis.title}".',
            user_id=jury_id,
            notification_type='jury_assigned',
            thesis_id=thesis.id
        )
        
        return thesis
    
    @staticmethod
    def search_thesis(query, status=None, career=None):
        """Buscar tesis por título, descripción o palabras clave"""
        search = f"%{query}%"
        thesis_query = Thesis.query.filter(
            db.or_(
                Thesis.title.ilike(search),
                Thesis.description.ilike(search),
                Thesis.keywords.ilike(search)
            )
        )
        
        if status:
            thesis_query = thesis_query.filter_by(status=status)
        
        if career:
            thesis_query = thesis_query.filter_by(career=career)
        
        return thesis_query.all()
    
    @staticmethod
    def get_thesis_statistics():
        """Obtener estadísticas de tesis"""
        total_thesis = Thesis.query.count()
        
        stats = {
            'total': total_thesis,
            'by_status': {},
            'by_career': {}
        }
        
        # Estadísticas por estado
        status_counts = db.session.query(
            Thesis.status, 
            db.func.count(Thesis.id)
        ).group_by(Thesis.status).all()
        
        for status, count in status_counts:
            stats['by_status'][status] = count
        
        # Estadísticas por carrera
        career_counts = db.session.query(
            Thesis.career, 
            db.func.count(Thesis.id)
        ).group_by(Thesis.career).all()
        
        for career, count in career_counts:
            stats['by_career'][career] = count
        
        return stats
    
    @staticmethod
    def remove_advisor(thesis_id):
        """Remover asesor de la tesis"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        thesis.advisor_id = None
        db.session.commit()
        return thesis
    
    @staticmethod
    def remove_jury(thesis_id):
        """Remover jurado de la tesis"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        thesis.jury_id = None
        db.session.commit()
        return thesis
    
    @staticmethod
    def change_status(thesis_id, new_status):
        """Cambiar estado de la tesis"""
        thesis = Thesis.query.get(thesis_id)
        if not thesis:
            raise ValueError("Tesis no encontrada")
        
        valid_statuses = ['draft', 'submitted', 'under_review', 'approved', 
                         'rejected', 'revision_required', 'completed']
        
        if new_status not in valid_statuses:
            raise ValueError("Estado no válido")
        
        old_status = thesis.status
        thesis.status = new_status
        
        # Actualizar fechas relevantes
        if new_status == 'submitted' and not thesis.submitted_at:
            thesis.submitted_at = datetime.utcnow()
        
        db.session.commit()
        
        # Crear notificación para el estudiante
        NotificationService.create_notification(
            title=f"Estado de tesis actualizado",
            message=f'Tu tesis "{thesis.title}" ha cambiado de estado a: {thesis.get_status_display()}.',
            user_id=thesis.student_id,
            notification_type='status_change',
            thesis_id=thesis.id
        )
        
        return thesis
