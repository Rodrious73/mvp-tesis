"""
Rutas para administradores
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services.thesis_service import ThesisService
from app.services.user_service import UserService
from app.services.document_service import DocumentService
from app.services.notification_service import NotificationService
from app.models.user import User

admin = Blueprint('admin', __name__)

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard del administrador"""
    # Obtener estadísticas generales
    thesis_stats = ThesisService.get_thesis_statistics()
    storage_stats = DocumentService.get_storage_statistics()
    
    # Contadores de usuarios
    total_users = User.query.filter_by(is_active=True).count()
    total_students = User.query.filter_by(role='student', is_active=True).count()
    total_teachers = User.query.filter_by(role='teacher', is_active=True).count()
    
    # Tesis recientes
    recent_thesis = ThesisService.get_thesis_by_status('submitted')[:5]
    
    return render_template('admin/dashboard.html',
                         thesis_stats=thesis_stats,
                         storage_stats=storage_stats,
                         total_users=total_users,
                         total_students=total_students,
                         total_teachers=total_teachers,
                         recent_thesis=recent_thesis)

@admin.route('/users')
@login_required
@admin_required
def users_list():
    """Lista de usuarios"""
    role_filter = request.args.get('role')
    search_query = request.args.get('search', '')
    
    if search_query:
        from app.services.user_service import search_users
        users = search_users(search_query, role_filter)
    elif role_filter:
        users = UserService.get_users_by_role(role_filter)
    else:
        users = UserService.get_active_users()
    
    return render_template('admin/users_list.html',
                         users=users,
                         role_filter=role_filter,
                         search_query=search_query)

@admin.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Detalle del usuario"""
    user = UserService.get_user_by_id(user_id)
    
    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('admin.users_list'))
    
    # Obtener tesis del usuario según su rol
    user_thesis = []
    if user.role == 'student':
        user_thesis = ThesisService.get_thesis_by_student(user_id)
    elif user.role == 'teacher':
        advisor_thesis = ThesisService.get_thesis_by_advisor(user_id)
        jury_thesis = ThesisService.get_thesis_by_jury(user_id)
        user_thesis = advisor_thesis + jury_thesis
    
    return render_template('admin/user_detail.html',
                         user=user,
                         user_thesis=user_thesis)

@admin.route('/users/<int:user_id>/toggle-status')
@login_required
@admin_required
def toggle_user_status(user_id):
    """Activar/desactivar usuario"""
    user = UserService.get_user_by_id(user_id)
    
    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('admin.users_list'))
    
    try:
        if user.is_active:
            UserService.deactivate_user(user_id)
            flash(f'Usuario {user.full_name} desactivado', 'info')
        else:
            UserService.activate_user(user_id)
            flash(f'Usuario {user.full_name} activado', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin.route('/thesis')
@login_required
@admin_required
def thesis_list():
    """Lista de todas las tesis"""
    status_filter = request.args.get('status')
    career_filter = request.args.get('career')
    search_query = request.args.get('search', '')
    
    if search_query:
        thesis_list = ThesisService.search_thesis(search_query, status_filter, career_filter)
    elif status_filter:
        thesis_list = ThesisService.get_thesis_by_status(status_filter)
    else:
        from app.models.thesis import Thesis
        thesis_list = Thesis.query.all()
    
    # Obtener carreras únicas para el filtro
    from app import db
    from app.models.thesis import Thesis
    careers = db.session.query(Thesis.career).distinct().all()
    careers = [career[0] for career in careers if career[0]]
    
    return render_template('admin/thesis_list.html',
                         thesis_list=thesis_list,
                         status_filter=status_filter,
                         career_filter=career_filter,
                         search_query=search_query,
                         careers=careers)

@admin.route('/thesis/<int:thesis_id>')
@login_required
@admin_required
def thesis_detail(thesis_id):
    """Detalle de la tesis"""
    thesis = ThesisService.get_thesis_by_id(thesis_id)
    
    if not thesis:
        flash('Tesis no encontrada', 'error')
        return redirect(url_for('admin.thesis_list'))
    
    # Obtener documentos
    documents = DocumentService.get_documents_by_thesis(thesis_id)
    
    # Obtener comentarios
    from app.models.comment import Comment
    comments = Comment.query.filter_by(thesis_id=thesis_id).order_by(Comment.created_at.desc()).all()
    
    return render_template('admin/thesis_detail.html',
                         thesis=thesis,
                         documents=documents,
                         comments=comments)

@admin.route('/thesis/<int:thesis_id>/assign-advisor', methods=['POST'])
@login_required
@admin_required
def assign_advisor(thesis_id):
    """Asignar asesor a la tesis"""
    advisor_id = request.form.get('advisor_id')
    
    if not advisor_id:
        flash('Debe seleccionar un asesor', 'error')
        return redirect(url_for('admin.thesis_detail', thesis_id=thesis_id))
    
    try:
        ThesisService.assign_advisor(thesis_id, int(advisor_id))
        flash('Asesor asignado exitosamente', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('admin.thesis_detail', thesis_id=thesis_id))

@admin.route('/thesis/<int:thesis_id>/assign-jury', methods=['POST'])
@login_required
@admin_required
def assign_jury(thesis_id):
    """Asignar jurado a la tesis"""
    jury_id = request.form.get('jury_id')
    
    if not jury_id:
        flash('Debe seleccionar un jurado', 'error')
        return redirect(url_for('admin.thesis_detail', thesis_id=thesis_id))
    
    try:
        ThesisService.assign_jury(thesis_id, int(jury_id))
        flash('Jurado asignado exitosamente', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('admin.thesis_detail', thesis_id=thesis_id))

@admin.route('/statistics')
@login_required
@admin_required
def statistics():
    """Página de estadísticas detalladas"""
    thesis_stats = ThesisService.get_thesis_statistics()
    storage_stats = DocumentService.get_storage_statistics()
    
    # Estadísticas de usuarios
    user_stats = {
        'total': User.query.filter_by(is_active=True).count(),
        'students': User.query.filter_by(role='student', is_active=True).count(),
        'teachers': User.query.filter_by(role='teacher', is_active=True).count(),
        'admins': User.query.filter_by(role='admin', is_active=True).count(),
    }
    
    return render_template('admin/statistics.html',
                         thesis_stats=thesis_stats,
                         storage_stats=storage_stats,
                         user_stats=user_stats)

@admin.route('/notifications/broadcast', methods=['GET', 'POST'])
@login_required
@admin_required
def broadcast_notification():
    """Enviar notificación masiva"""
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        target_role = request.form.get('target_role')
        
        if not all([title, message]):
            flash('Título y mensaje son requeridos', 'error')
            return render_template('admin/broadcast_notification.html')
        
        # Obtener usuarios objetivo
        if target_role == 'all':
            target_users = UserService.get_active_users()
        else:
            target_users = UserService.get_users_by_role(target_role)
        
        user_ids = [user.id for user in target_users]
        
        try:
            NotificationService.create_bulk_notification(
                title=title,
                message=message,
                user_ids=user_ids,
                notification_type='system_message'
            )
            
            flash(f'Notificación enviada a {len(user_ids)} usuarios', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            flash('Error al enviar notificación', 'error')
    
    return render_template('admin/broadcast_notification.html')

@admin.route('/api/teachers')
@login_required
@admin_required
def api_teachers():
    """API para obtener lista de docentes"""
    from app.services.user_service import get_teachers
    teachers = get_teachers()
    return jsonify([{
        'id': teacher.id,
        'name': teacher.full_name,
        'department': teacher.department,
        'specialization': teacher.specialization
    } for teacher in teachers])

@admin.route('/api/thesis-stats')
@login_required
@admin_required
def api_thesis_stats():
    """API para obtener estadísticas de tesis"""
    stats = ThesisService.get_thesis_statistics()
    return jsonify(stats)

@admin.route('/thesis/<int:thesis_id>/remove-advisor', methods=['POST'])
@login_required
@admin_required
def remove_advisor(thesis_id):
    """Remover asesor de la tesis"""
    try:
        ThesisService.remove_advisor(thesis_id)
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@admin.route('/thesis/<int:thesis_id>/remove-jury', methods=['POST'])
@login_required
@admin_required
def remove_jury(thesis_id):
    """Remover jurado de la tesis"""
    try:
        ThesisService.remove_jury(thesis_id)
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@admin.route('/thesis/<int:thesis_id>/change-status', methods=['POST'])
@login_required
@admin_required
def change_thesis_status(thesis_id):
    """Cambiar estado de la tesis"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'success': False, 'error': 'Estado requerido'}), 400
        
        ThesisService.change_status(thesis_id, new_status)
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@admin.route('/download-document/<int:document_id>')
@login_required
@admin_required
def download_document(document_id):
    """Descargar documento"""
    try:
        return DocumentService.download_document(document_id)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('admin.thesis_list'))
