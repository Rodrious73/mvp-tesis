"""
Modelos de base de datos
"""

from .user import User
from .thesis import Thesis
from .document import Document
from .notification import Notification
from .comment import Comment

__all__ = ['User', 'Thesis', 'Document', 'Notification', 'Comment']
