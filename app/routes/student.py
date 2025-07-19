"""
Rutas para estudiantes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app.services.thesis_service import ThesisService
from app.services.document_service import DocumentService
from app.services.notification_service import NotificationService
from app.models.comment import Comment
from app import db

student = Blueprint('student', __name__)

def student_required(f):
    """Decorador para requerir rol de estudiante"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Acceso denegado', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@student.route('/dashboard')
@login_required
@student_required
def dashboard():
    """Dashboard del estudiante"""
    # Obtener tesis del estudiante
    thesis_list = ThesisService.get_thesis_by_student(current_user.id)
    current_thesis = thesis_list[0] if thesis_list else None
    
    # Obtener notificaciones recientes
    notifications = NotificationService.get_user_notifications(
        current_user.id, 
        limit=5
    )
    
    # Obtener documentos si hay tesis
    documents = []
    if current_thesis:
        documents = DocumentService.get_documents_by_thesis(current_thesis.id)
    
    return render_template('student/dashboard.html', 
                         thesis=current_thesis,
                         documents=documents,
                         notifications=notifications)

@student.route('/thesis/new', methods=['GET', 'POST'])
@login_required
@student_required
def new_thesis():
    """Crear nueva propuesta de tesis"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        career = request.form.get('career')
        research_line = request.form.get('research_line')
        keywords = request.form.get('keywords')
        action = request.form.get('action', 'save_draft')
        
        if not all([title, career]):
            flash('Título y carrera son requeridos', 'error')
            return render_template('student/new_thesis.html')
        
        try:
            thesis = ThesisService.create_thesis(
                title=title,
                student_id=current_user.id,
                career=career,
                description=description,
                research_line=research_line,
                keywords=keywords
            )
            
            # Procesar archivos si se subieron
            files_uploaded = []
            
            # Archivo de propuesta
            if 'proposal_file' in request.files:
                proposal_file = request.files['proposal_file']
                if proposal_file and proposal_file.filename:
                    try:
                        document = DocumentService.save_file(
                            file=proposal_file,
                            thesis_id=thesis.id,
                            uploaded_by=current_user.id,
                            document_type='proposal'
                        )
                        files_uploaded.append('Propuesta')
                    except Exception as e:
                        flash(f'Error al subir propuesta: {str(e)}', 'warning')
            
            # Archivo adicional
            if 'additional_file' in request.files:
                additional_file = request.files['additional_file']
                if additional_file and additional_file.filename:
                    try:
                        document = DocumentService.save_file(
                            file=additional_file,
                            thesis_id=thesis.id,
                            uploaded_by=current_user.id,
                            document_type='additional'
                        )
                        files_uploaded.append('Documento adicional')
                    except Exception as e:
                        flash(f'Error al subir documento adicional: {str(e)}', 'warning')
            
            # Cambiar estado si se va a presentar
            if action == 'submit':
                ThesisService.submit_thesis(thesis.id)
                message = 'Propuesta de tesis presentada para revisión exitosamente'
            else:
                message = 'Propuesta de tesis guardada como borrador exitosamente'
            
            if files_uploaded:
                message += f'. Archivos subidos: {", ".join(files_uploaded)}'
            
            flash(message, 'success')
            return redirect(url_for('student.thesis_detail', thesis_id=thesis.id))
            
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('student/new_thesis.html')

@student.route('/thesis/<int:thesis_id>')
@login_required
@student_required
def thesis_detail(thesis_id):
    """Detalle de la tesis"""
    thesis = ThesisService.get_thesis_by_id(thesis_id)
    
    if not thesis or thesis.student_id != current_user.id:
        flash('Tesis no encontrada', 'error')
        return redirect(url_for('student.dashboard'))
    
    # Obtener documentos
    documents = DocumentService.get_documents_by_thesis(thesis_id)
    
    # Obtener comentarios
    comments = Comment.query.filter_by(thesis_id=thesis_id).order_by(Comment.created_at.desc()).all()
    
    return render_template('student/thesis_detail.html',
                         thesis=thesis,
                         documents=documents,
                         comments=comments)

@student.route('/thesis/<int:thesis_id>/edit', methods=['GET', 'POST'])
@login_required
@student_required
def edit_thesis(thesis_id):
    """Editar tesis"""
    thesis = ThesisService.get_thesis_by_id(thesis_id)
    
    if not thesis or thesis.student_id != current_user.id:
        flash('Tesis no encontrada', 'error')
        return redirect(url_for('student.dashboard'))
    
    if not thesis.can_be_edited_by(current_user):
        flash('No puedes editar esta tesis en su estado actual', 'error')
        return redirect(url_for('student.thesis_detail', thesis_id=thesis_id))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        research_line = request.form.get('research_line')
        keywords = request.form.get('keywords')
        
        try:
            ThesisService.update_thesis(
                thesis_id,
                title=title,
                description=description,
                research_line=research_line,
                keywords=keywords
            )
            
            flash('Tesis actualizada exitosamente', 'success')
            return redirect(url_for('student.thesis_detail', thesis_id=thesis_id))
            
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('student/thesis_edit.html', thesis=thesis)

@student.route('/thesis/<int:thesis_id>/submit')
@login_required
@student_required
def submit_thesis(thesis_id):
    """Presentar tesis para revisión"""
    thesis = ThesisService.get_thesis_by_id(thesis_id)
    
    if not thesis or thesis.student_id != current_user.id:
        flash('Tesis no encontrada', 'error')
        return redirect(url_for('student.dashboard'))
    
    try:
        ThesisService.submit_thesis(thesis_id)
        flash('Tesis presentada para revisión exitosamente', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('student.thesis_detail', thesis_id=thesis_id))

@student.route('/thesis/<int:thesis_id>/upload', methods=['POST'])
@login_required
@student_required
def upload_document(thesis_id):
    """Subir documento"""
    thesis = ThesisService.get_thesis_by_id(thesis_id)
    
    if not thesis or thesis.student_id != current_user.id:
        flash('Tesis no encontrada', 'error')
        return redirect(url_for('student.dashboard'))
    
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('student.thesis_detail', thesis_id=thesis_id))
    
    file = request.files['file']
    document_type = request.form.get('document_type', 'other')
    description = request.form.get('description', '')
    
    try:
        document = DocumentService.save_file(
            file=file,
            thesis_id=thesis_id,
            uploaded_by=current_user.id,
            document_type=document_type,
            description=description
        )
        
        flash(f'Documento "{document.original_filename}" subido exitosamente', 'success')
        
    except ValueError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('student.thesis_detail', thesis_id=thesis_id))

@student.route('/notifications')
@login_required
@student_required
def notifications():
    """Ver todas las notificaciones"""
    notifications = NotificationService.get_user_notifications(current_user.id)
    
    return render_template('student/notifications.html', 
                         notifications=notifications)

@student.route('/notifications/<int:notification_id>/read')
@login_required
@student_required
def mark_notification_read(notification_id):
    """Marcar notificación como leída"""
    notification = NotificationService.mark_as_read(notification_id)
    
    if notification and notification.user_id == current_user.id:
        if notification.action_url:
            return redirect(notification.action_url)
    
    return redirect(url_for('student.notifications'))

@student.route('/download/<int:document_id>')
@login_required
@student_required
def download_document(document_id):
    """Descargar documento"""
    document = DocumentService.get_document_by_id(document_id)
    
    if not document:
        flash('Documento no encontrado', 'error')
        return redirect(url_for('student.dashboard'))
    
    # Verificar que el estudiante puede acceder al documento
    if document.thesis.student_id != current_user.id:
        flash('No tienes permiso para descargar este documento', 'error')
        return redirect(url_for('student.dashboard'))
    
    file_path = DocumentService.get_file_path(document_id)
    if file_path:
        return send_file(file_path, as_attachment=True, 
                        download_name=document.original_filename)
    
    flash('Archivo no encontrado', 'error')
    return redirect(url_for('student.dashboard'))

@student.route('/api/notifications/unread-count')
@login_required
@student_required
def unread_notifications_count():
    """API para obtener número de notificaciones no leídas"""
    count = NotificationService.get_unread_count(current_user.id)
    return jsonify({'count': count})
