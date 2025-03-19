from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from models.document import Document
from models.submission import Submission
from models.user import User
from services.document_service import verify_document_on_blockchain
from services.grade_service import verify_grade

blockchain = Blueprint('blockchain', __name__)

@blockchain.route('/verify_document/<int:document_id>')
def verify_document(document_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    document = Document.query.get_or_404(document_id)
    user = User.query.get(session['user_id'])

    # Check permission (document owner or teacher for submissions)
    has_permission = False

    # Document owner can always verify
    if document.user_id == user.id:
        has_permission = True

    # Teacher can verify student submissions for their assignments
    if user.role == 'teacher':
        submission = Submission.query.filter_by(document_id=document_id).first()
        if submission and submission.assignment.teacher_id == user.id:
            has_permission = True

    if not has_permission:
        flash('You do not have permission to verify this document', 'danger')
        return redirect(url_for('auth.index'))

    is_verified = verify_document_on_blockchain(document_id)

    if is_verified:
        flash('Document verified on blockchain!', 'success')
    else:
        flash('Document verification failed - hash not found on blockchain', 'danger')

    # Redirect based on document type and user role
    if user.role == 'student':
        return redirect(url_for('student.view_documents'))
    else:
        submission = Submission.query.filter_by(document_id=document_id).first()
        if submission:
            return redirect(url_for('teacher.view_submission', submission_id=submission.id))
        else:
            return redirect(url_for('teacher.view_documents'))  # Changed from 'teacher.documents'

@blockchain.route('/verify_grade/<int:submission_id>')
def verify_grade_route(submission_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    submission = Submission.query.get_or_404(submission_id)
    user = User.query.get(session['user_id'])

    # Check permission
    has_permission = False

    # Student can verify their own grades
    if user.role == 'student' and submission.student_id == user.id:
        has_permission = True

    # Teacher can verify grades for their assignments
    if user.role == 'teacher' and submission.assignment.teacher_id == user.id:
        has_permission = True

    if not has_permission:
        flash('You do not have permission to verify this grade', 'danger')
        return redirect(url_for('auth.index'))

    if submission.status != 'graded':
        flash('This submission has not been graded yet', 'warning')
        if user.role == 'student':
            return redirect(url_for('student.view_submission', submission_id=submission.id))
        else:
            return redirect(url_for('teacher.view_submission', submission_id=submission.id))

    grade_verified = verify_grade(submission.id)

    if grade_verified:
        flash('Grade verified on blockchain!', 'success')
    else:
        flash('Grade verification failed', 'danger')

    # Redirect based on user role
    if user.role == 'student':
        return redirect(url_for('student.view_submission', submission_id=submission.id))
    else:
        return redirect(url_for('teacher.view_submission', submission_id=submission.id))

@blockchain.route('/api/document_info/<int:document_id>')
def document_info(document_id):
    """API endpoint to get document blockchain info"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    document = Document.query.get_or_404(document_id)

    # Simple permission check
    user = User.query.get(session['user_id'])
    if document.user_id != user.id and user.role != 'teacher':
        return jsonify({'error': 'Permission denied'}), 403

    return jsonify({
        'id': document.id,
        'filename': document.original_filename,
        'hash': document.hash,
        'blockchain_tx': document.blockchain_tx,
        'nft_token_id': document.nft_token_id,
        'uploaded_at': document.uploaded_at.isoformat(),
        'is_verified': verify_document_on_blockchain(document.id)
    })