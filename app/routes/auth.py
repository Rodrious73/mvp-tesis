"""
Rutas de autenticación
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service import AuthService
from app.services.user_service import UserService

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Email y contraseña son requeridos', 'error')
            return render_template('auth/login.html')
        
        user = AuthService.authenticate_user(email, password)
        
        if user == 'locked':
            flash('Tu cuenta está temporalmente bloqueada debido a múltiples intentos fallidos. Inténtalo de nuevo en 30 minutos.', 'error')
            return render_template('auth/login.html')
        elif user:
            login_user(user, remember=remember)
            flash(f'¡Bienvenido, {user.first_name}!', 'success')
            
            # Redirigir a la página solicitada o al dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redirigir según el rol
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student.dashboard'))
        else:
            flash('Email o contraseña incorrectos', 'error')
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Obtener datos del formulario
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role', 'student')
        
        # Validaciones básicas
        if not all([email, password, first_name, last_name]):
            flash('Todos los campos son requeridos', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('auth/register.html')
        
        # Datos adicionales según el rol
        additional_data = {}
        
        if role == 'student':
            additional_data['student_code'] = request.form.get('student_code')
            additional_data['career'] = request.form.get('career')
        elif role == 'teacher':
            additional_data['department'] = request.form.get('department')
            additional_data['specialization'] = request.form.get('specialization')
        
        try:
            # Crear usuario
            user = UserService.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                **additional_data
            )
            
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
            
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('main.index'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Perfil del usuario"""
    if request.method == 'POST':
        # Actualizar información del perfil
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        
        update_data = {
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone
        }
        
        # Datos adicionales según el rol
        if current_user.role == 'student':
            update_data['career'] = request.form.get('career')
        elif current_user.role == 'teacher':
            update_data['department'] = request.form.get('department')
            update_data['specialization'] = request.form.get('specialization')
        
        try:
            UserService.update_user(current_user.id, **update_data)
            flash('Perfil actualizado exitosamente', 'success')
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('auth/profile.html')

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambiar contraseña"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validaciones
        if not current_user.check_password(current_password):
            flash('Contraseña actual incorrecta', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('Las nuevas contraseñas no coinciden', 'error')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('auth/change_password.html')
        
        try:
            UserService.change_password(current_user.id, new_password)
            flash('Contraseña cambiada exitosamente', 'success')
            return redirect(url_for('auth.profile'))
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('auth/change_password.html')

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Solicitar recuperación de contraseña"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email es requerido', 'error')
            return render_template('auth/forgot_password.html')
        
        result = AuthService.request_password_reset(email)
        
        if result:
            user, token = result
            # En un entorno de producción, aquí enviarías un email
            # Por ahora mostraremos un mensaje de éxito genérico
            flash('Si el email existe en nuestro sistema, recibirás instrucciones para recuperar tu contraseña.', 'info')
            # Para desarrollo, mostramos el token en un flash (REMOVER EN PRODUCCIÓN)
            flash(f'Token de recuperación (desarrollo): {token}', 'warning')
        else:
            # Siempre mostramos el mismo mensaje por seguridad
            flash('Si el email existe en nuestro sistema, recibirás instrucciones para recuperar tu contraseña.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Resetear contraseña con token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Todos los campos son requeridos', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if AuthService.reset_password_with_token(token, password):
            flash('Contraseña actualizada exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Token inválido o expirado', 'error')
            return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/reset_password.html', token=token)

@auth.route('/api/check-email')
def check_email():
    """API para verificar si un email ya está registrado"""
    email = request.args.get('email')
    if not email:
        return jsonify({'exists': False})
    
    user = UserService.get_user_by_email(email)
    return jsonify({'exists': user is not None})
