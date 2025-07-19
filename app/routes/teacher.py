"""
Rutas para docentes
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app.services.thesis_service import ThesisService
from app.services.document_service import DocumentService
from app.services.notification_service import NotificationService
from app.models.comment import Comment
from app import db

teacher = Blueprint('teacher', __name__)

def teacher_required(f):
    """Decorador para requerir rol de docente"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['teacher', 'admin']:
            flash('Acceso denegado', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@teacher.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    """Dashboard del docente"""
    # Obtener tesis como asesor
    thesis_as_advisor = ThesisService.get_thesis_by_advisor(current_user.id)
    
    # Obtener tesis como jurado
    thesis_as_jury = ThesisService.get_thesis_by_jury(current_user.id)
    
    # Obtener tesis pendientes de revisión
    pending_thesis = []
    for thesis in thesis_as_advisor + thesis_as_jury:
        if thesis.status in ['submitted', 'under_review']:
            pending_thesis.append(thesis)
    
    # Obtener notificaciones recientes
    notifications = NotificationService.get_user_notifications(
        current_user.id, 
        limit=5
    )
    
    return render_template('teacher/dashboard.html',
                         thesis_as_advisor=thesis_as_advisor,
                         thesis_as_jury=thesis_as_jury,
                         pending_thesis=pending_thesis,
                         notifications=notifications,
                         current_date=datetime.now())

@teacher.route('/thesis')
@login_required
@teacher_required
def thesis_list():
    """Lista de todas las tesis asignadas"""
    # Obtener tesis como asesor
    thesis_as_advisor = ThesisService.get_thesis_by_advisor(current_user.id)
    
    # Obtener tesis como jurado
    thesis_as_jury = ThesisService.get_thesis_by_jury(current_user.id)
    
    # Filtros
    status_filter = request.args.get('status')
    
    if status_filter:
        thesis_as_advisor = [t for t in thesis_as_advisor if t.status == status_filter]
        thesis_as_jury = [t for t in thesis_as_jury if t.status == status_filter]
    
    return render_template('teacher/thesis_list.html',
                         thesis_as_advisor=thesis_as_advisor,
                         thesis_as_jury=thesis_as_jury,
                         status_filter=status_filter)

@teacher.route('/thesis/<int:thesis_id>')
@login_required
@teacher_required
def thesis_detail(thesis_id):
    """Detalle de la tesis"""
    thesis = ThesisService.get_thesis_by_id(thesis_id)
    
    if not thesis:
        flash('Tesis no encontrada', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    # Verificar que el docente puede ver esta tesis
    if not thesis.can_be_reviewed_by(current_user):
        flash('No tienes permiso para ver esta tesis', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    # Obtener documentos
    documents = DocumentService.get_documents_by_thesis(thesis_id)
    
    # Obtener comentarios
    comments = Comment.query.filter_by(thesis_id=thesis_id).order_by(Comment.created_at.desc()).all()
    
    return render_template('teacher/thesis_detail.html',
                         thesis=thesis,
                         documents=documents,
                         comments=comments)

@teacher.route('/thesis/<int:thesis_id>/review', methods=['GET', 'POST'])
@login_required
@teacher_required
def review_thesis(thesis_id):
    """Revisar tesis"""
    thesis = ThesisService.get_thesis_by_id(thesis_id)
    
    if not thesis or not thesis.can_be_reviewed_by(current_user):
        flash('No tienes permiso para revisar esta tesis', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        comment_content = request.form.get('comment')
        comment_type = request.form.get('comment_type', 'general')
        grade = request.form.get('grade')
        
        try:
            # Iniciar revisión si no está en revisión
            if thesis.status == 'submitted':
                ThesisService.start_review(thesis_id, current_user.id)
            
            # Agregar comentario si se proporcionó
            if comment_content:
                comment = Comment(
                    content=comment_content,
                    thesis_id=thesis_id,
                    author_id=current_user.id,
                    comment_type=comment_type
                )
                db.session.add(comment)
                
                # Crear notificación para el estudiante
                NotificationService.create_notification(
                    title="Nuevo comentario en tu tesis",
                    message=f'Se agregó un nuevo comentario en tu tesis "{thesis.title}".',
                    user_id=thesis.student_id,
                    notification_type='new_comment',
                    thesis_id=thesis_id
                )
            
            # Realizar acción según el botón presionado
            if action == 'approve':
                ThesisService.approve_thesis(thesis_id, current_user.id, grade)
                flash('Tesis aprobada exitosamente', 'success')
            elif action == 'reject':
                ThesisService.reject_thesis(thesis_id, current_user.id)
                flash('Tesis rechazada', 'info')
            elif action == 'require_revision':
                ThesisService.require_revision(thesis_id, current_user.id)
                flash('Se ha solicitado revisión de la tesis', 'info')
            elif comment_content:
                flash('Comentario agregado exitosamente', 'success')
            
            db.session.commit()
            
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'error')
    
    # Obtener comentarios
    comments = Comment.query.filter_by(thesis_id=thesis_id).order_by(Comment.created_at.desc()).all()
    
    return render_template('teacher/review_thesis.html',
                         thesis=thesis,
                         comments=comments)

@teacher.route('/thesis/<int:thesis_id>/comment', methods=['POST'])
@login_required
@teacher_required
def add_comment(thesis_id):
    """Agregar comentario a la tesis"""
    thesis = ThesisService.get_thesis_by_id(thesis_id)
    
    if not thesis or not thesis.can_be_reviewed_by(current_user):
        flash('No tienes permiso para comentar esta tesis', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    content = request.form.get('content')
    comment_type = request.form.get('comment_type', 'general')
    is_private = bool(request.form.get('is_private'))
    
    if not content:
        flash('El comentario no puede estar vacío', 'error')
        return redirect(url_for('teacher.thesis_detail', thesis_id=thesis_id))
    
    try:
        comment = Comment(
            content=content,
            thesis_id=thesis_id,
            author_id=current_user.id,
            comment_type=comment_type,
            is_private=is_private
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # Crear notificación para el estudiante
        NotificationService.create_notification(
            title="Nuevo comentario en tu tesis",
            message=f'Se agregó un nuevo comentario en tu tesis "{thesis.title}".',
            user_id=thesis.student_id,
            notification_type='new_comment',
            thesis_id=thesis_id
        )
        
        flash('Comentario agregado exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error al agregar comentario', 'error')
    
    return redirect(url_for('teacher.thesis_detail', thesis_id=thesis_id))

@teacher.route('/notifications')
@login_required
@teacher_required
def notifications():
    """Ver todas las notificaciones"""
    notifications = NotificationService.get_user_notifications(current_user.id)
    
    return render_template('teacher/notifications.html', 
                         notifications=notifications)

@teacher.route('/notifications/<int:notification_id>/read')
@login_required
@teacher_required
def mark_notification_read(notification_id):
    """Marcar notificación como leída"""
    notification = NotificationService.mark_as_read(notification_id)
    
    if notification and notification.user_id == current_user.id:
        if notification.action_url:
            return redirect(notification.action_url)
    
    return redirect(url_for('teacher.notifications'))

@teacher.route('/download/<int:document_id>')
@login_required
@teacher_required
def download_document(document_id):
    """Descargar documento"""
    document = DocumentService.get_document_by_id(document_id)
    
    if not document:
        flash('Documento no encontrado', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    # Verificar que el docente puede acceder al documento
    if not document.thesis.can_be_reviewed_by(current_user):
        flash('No tienes permiso para descargar este documento', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    file_path = DocumentService.get_file_path(document_id)
    if file_path:
        return send_file(file_path, as_attachment=True, 
                        download_name=document.original_filename)
    
    flash('Archivo no encontrado', 'error')
    return redirect(url_for('teacher.dashboard'))

@teacher.route('/api/notifications/unread-count')
@login_required
@teacher_required
def unread_notifications_count():
    """API para obtener número de notificaciones no leídas"""
    count = NotificationService.get_unread_count(current_user.id)
    return jsonify({'count': count})
