"""
Servicio de notificaciones
"""

from app import db
from app.models.notification import Notification

class NotificationService:
    """Servicio para manejar notificaciones"""
    
    @staticmethod
    def create_notification(title, message, user_id, notification_type='system_message', 
                          thesis_id=None, action_url=None):
        """Crear una nueva notificación"""
        notification = Notification(
            title=title,
            message=message,
            user_id=user_id,
            notification_type=notification_type,
            thesis_id=thesis_id,
            action_url=action_url
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    @staticmethod
    def get_user_notifications(user_id, unread_only=False, limit=None):
        """Obtener notificaciones de un usuario"""
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        query = query.order_by(Notification.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def mark_as_read(notification_id):
        """Marcar notificación como leída"""
        notification = Notification.query.get(notification_id)
        if notification:
            notification.mark_as_read()
            return notification
        return None
    
    @staticmethod
    def mark_as_unread(notification_id):
        """Marcar notificación como no leída"""
        notification = Notification.query.get(notification_id)
        if notification:
            notification.mark_as_unread()
            return notification
        return None
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Marcar todas las notificaciones como leídas"""
        notifications = Notification.query.filter_by(
            user_id=user_id, 
            is_read=False
        ).all()
        
        for notification in notifications:
            notification.mark_as_read()
        
        return len(notifications)
    
    @staticmethod
    def delete_notification(notification_id):
        """Eliminar notificación"""
        notification = Notification.query.get(notification_id)
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_unread_count(user_id):
        """Obtener número de notificaciones no leídas"""
        return Notification.query.filter_by(
            user_id=user_id, 
            is_read=False
        ).count()
    
    @staticmethod
    def create_thesis_notification(notification_type, thesis, recipient_user, **kwargs):
        """Crear notificación relacionada con tesis usando el método del modelo"""
        return Notification.create_thesis_notification(
            notification_type, thesis, recipient_user, **kwargs
        )
    
    @staticmethod
    def create_bulk_notification(title, message, user_ids, notification_type='system_message'):
        """Crear notificación para múltiples usuarios"""
        notifications = []
        
        for user_id in user_ids:
            notification = Notification(
                title=title,
                message=message,
                user_id=user_id,
                notification_type=notification_type
            )
            notifications.append(notification)
        
        db.session.add_all(notifications)
        db.session.commit()
        
        return notifications
    
    @staticmethod
    def clean_old_notifications(days=30):
        """Limpiar notificaciones antiguas"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Eliminar notificaciones leídas antiguas
        old_notifications = Notification.query.filter(
            Notification.is_read == True,
            Notification.created_at < cutoff_date
        ).all()
        
        count = len(old_notifications)
        
        for notification in old_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        
        return count
