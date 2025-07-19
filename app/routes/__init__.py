"""
Rutas de la aplicación
"""

from .main import main
from .auth import auth
from .student import student
from .teacher import teacher
from .admin import admin

__all__ = ['main', 'auth', 'student', 'teacher', 'admin']
