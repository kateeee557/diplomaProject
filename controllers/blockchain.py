from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from models.document import Document
from models.submission import Submission
from models.user import User
from services.document_service import verify_document_on_blockchain
from services.grade_service import verify_grade
from services.blockchain_service import get_blockchain_service
import logging

logger = logging.getLogger(__name__)

blockchain = Blueprint('blockchain', __name__)

@blockchain.route('/status')
def blockchain_status():
    """Check blockchain connection status"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    try:
        blockchain_service = get_blockchain_service()
        if not blockchain_service:
            status = {
                'connected': False,
                'message': 'Blockchain service not initialized'
            }
        elif blockchain_service.offline_mode:
            status = {
                'connected': False,
                'message': 'Running in offline mode - blockchain features simulated'
            }
        else:
            # Check if connected to blockchain
            status = {
                'connected': True,
                'provider': blockchain_service.w3.provider._request_kwargs['endpoint_uri'],
                'contracts': {
                    'token': blockchain_service.token_address != None,
                    'document': blockchain_service.document_address != None,
                    'wallet_factory': blockchain_service.wallet_factory_address != None,
                    'token_tracker': blockchain_service.token_tracker_address != None
                }
            }
    except Exception as e:
        logger.error(f"Error checking blockchain status: {e}")
        status = {
            'connected': False,
            'error': str(e)
        }

    return render_template('blockchain/status.html', status=status)

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

    # Check if blockchain service is available
    blockchain_service = get_blockchain_service()
    if not blockchain_service:
        flash('Blockchain verification service is not available at the moment', 'warning')
        # Redirect based on document type and user role
        if user.role == 'student':
            return redirect(url_for('student.view_documents'))
        else:
            submission = Submission.query.filter_by(document_id=document_id).first()
            if submission:
                return redirect(url_for('teacher.view_submission', submission_id=submission.id))
            else:
                return redirect(url_for('teacher.view_documents'))

    is_verified = verify_document_on_blockchain(document_id)

    if is_verified:
        flash('Document verified on blockchain!', 'success')
    else:
        if blockchain_service.offline_mode:
            flash('Running in offline mode - blockchain verification simulated', 'warning')
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
            return redirect(url_for('teacher.view_documents'))

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

    # Check if blockchain service is available
    blockchain_service = get_blockchain_service()
    if not blockchain_service:
        flash('Blockchain verification service is not available at the moment', 'warning')
        if user.role == 'student':
            return redirect(url_for('student.view_submission', submission_id=submission.id))
        else:
            return redirect(url_for('teacher.view_submission', submission_id=submission.id))

    grade_verified = verify_grade(submission.id)

    if grade_verified:
        flash('Grade verified on blockchain!', 'success')
    else:
        if blockchain_service.offline_mode:
            flash('Running in offline mode - grade verification simulated', 'warning')
        else:
            flash('Grade verification failed - record not found on blockchain', 'danger')

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

    # Check if blockchain service is available
    blockchain_service = get_blockchain_service()
    if not blockchain_service:
        return jsonify({
            'id': document.id,
            'filename': document.original_filename,
            'hash': document.hash,
            'blockchain_tx': document.blockchain_tx,
            'nft_token_id': document.nft_token_id,
            'uploaded_at': document.uploaded_at.isoformat(),
            'is_verified': False,
            'blockchain_status': 'unavailable'
        })

    verification_result = verify_document_on_blockchain(document.id)

    return jsonify({
        'id': document.id,
        'filename': document.original_filename,
        'hash': document.hash,
        'blockchain_tx': document.blockchain_tx,
        'nft_token_id': document.nft_token_id,
        'uploaded_at': document.uploaded_at.isoformat(),
        'is_verified': verification_result,
        'blockchain_status': 'offline' if blockchain_service.offline_mode else 'online'
    })