"""
Rutas principales de la aplicación
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Página principal"""
    if current_user.is_authenticated:
        # Redirigir según el rol del usuario
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif current_user.role == 'student':
            return redirect(url_for('student.dashboard'))
    
    return render_template('index.html')

@main.route('/about')
def about():
    """Página acerca de"""
    return render_template('about.html')

@main.route('/contact')
def contact():
    """Página de contacto"""
    return render_template('contact.html')

@main.route('/help')
def help():
    """Página de ayuda"""
    return render_template('help.html')
