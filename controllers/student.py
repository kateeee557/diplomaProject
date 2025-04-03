from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_from_directory, current_app
from datetime import datetime
import os
import uuid
import hashlib
from app import db
from models.user import User
from models.assignment import Assignment
from models.document import Document
from models.submission import Submission
from models.integrity_violation import IntegrityViolation
from services.document_service import save_uploaded_file, hash_file, detect_document_similarity
from services.token_service import get_token_balance, get_user_transactions
from services.blockchain_service import get_blockchain_service

student = Blueprint('student', __name__)

@student.before_request
def check_student():
    # Ensure user is logged in and is a student
    if 'user_id' not in session or session['role'] != 'student':
        flash('Please log in as a student to access this page', 'warning')
        return redirect(url_for('auth.login'))

@student.route('/dashboard')
def dashboard():
    user = User.query.get(session['user_id'])

    # Get upcoming assignments
    upcoming_assignments = Assignment.query.filter(
        Assignment.deadline >= datetime.utcnow()
    ).order_by(Assignment.deadline).limit(5).all()

    # Get submissions with grades
    recent_grades = Submission.query.filter_by(
        student_id=user.id,
        status='graded'
    ).order_by(Submission.graded_at.desc()).limit(5).all()

    # Get token balance
    token_balance = get_token_balance(user.id)
    token_percentage = min(int(token_balance / 100 * 100), 100)  # Scale for progress bar

    return render_template(
        'student/dashboard.html',
        user=user,
        upcoming_assignments=upcoming_assignments,
        recent_grades=recent_grades,
        token_balance=token_balance,
        token_percentage=token_percentage,
        now=datetime.utcnow()
    )

@student.route('/assignments')
def view_assignments():
    user = User.query.get(session['user_id'])

    # Get all assignments
    assignments = Assignment.query.order_by(Assignment.deadline).all()

    # Mark assignments as submitted if they were
    user_submissions = {s.assignment_id: s for s in Submission.query.filter_by(student_id=user.id).all()}

    for assignment in assignments:
        if assignment.id in user_submissions:
            assignment.submitted = True
            assignment.submission = user_submissions[assignment.id]
        else:
            assignment.submitted = False

    return render_template(
        'student/assignments.html',
        assignments=assignments,
        user=user,
        now=datetime.utcnow()
    )

@student.route('/submit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
def submit_assignment(assignment_id):
    user = User.query.get(session['user_id'])
    assignment = Assignment.query.get_or_404(assignment_id)

    # Check if student already submitted
    existing_submission = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=user.id
    ).first()

    if request.method == 'POST':
        # Only allow new submission if none exists
        if existing_submission:
            flash('You have already submitted this assignment', 'warning')
            return redirect(url_for('student.view_assignments'))

        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return render_template('student/submit_assignment.html', assignment=assignment, user=user, now=datetime.utcnow())

        file = request.files['file']

        if file.filename == '':
            flash('No file selected', 'danger')
            return render_template('student/submit_assignment.html', assignment=assignment, user=user, now=datetime.utcnow())

        # Get deadline in Unix timestamp
        deadline_timestamp = int(assignment.deadline.timestamp())

        # Save document and mint NFT
        document = save_uploaded_file(
            file=file,
            document_type='assignment_submission',
            user_id=user.id,
            is_assignment=True,
            deadline=deadline_timestamp
        )

        if document:
            # Create submission record
            submission = Submission(
                assignment_id=assignment.id,
                student_id=user.id,
                document_id=document.id,
                submitted_at=datetime.utcnow(),
                status='submitted'
            )

            db.session.add(submission)
            db.session.commit()

            # Check if on-time
            on_time = datetime.utcnow() <= assignment.deadline
            if on_time:
                flash('Assignment submitted on time! 10 tokens awarded!', 'success')
            else:
                flash('Assignment submitted, but after the deadline (no tokens awarded)', 'warning')

            return redirect(url_for('student.view_assignments'))
        else:
            # Check if this was a duplicate document
            # Create a temporary file to get the hash
            temp_file = file
            temp_file.seek(0)  # Reset file pointer

            # Save to a temporary location
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_check_' + str(uuid.uuid4()))
            temp_file.save(temp_path)

            # Calculate hash
            temp_hash = hash_file(temp_path)

            # Remove temporary file
            os.remove(temp_path)

            # Check if this hash exists in the database
            existing_doc = Document.query.filter_by(hash=temp_hash).first()

            if existing_doc:
                # It's a duplicate document
                existing_owner = User.query.get(existing_doc.user_id)

                if existing_owner.id == user.id:
                    flash('You have already uploaded this document. Please submit a different file.', 'warning')
                else:
                    flash('This document appears to be identical to one already in the system. This has been flagged as a potential academic integrity violation.', 'danger')
            else:
                flash('Error saving submission. Please try again.', 'danger')

    # GET request - show submission form
    return render_template(
        'student/submit_assignment.html',
        assignment=assignment,
        existing_submission=existing_submission,
        user=user,
        now=datetime.utcnow()
    )

@student.route('/view_submission/<int:submission_id>')
def view_submission(submission_id):
    user = User.query.get(session['user_id'])
    submission = Submission.query.get_or_404(submission_id)

    # Ensure this is the student's submission
    if submission.student_id != user.id:
        flash('You do not have permission to view this submission', 'danger')
        return redirect(url_for('student.view_assignments'))

    # Use the standard relationship attributes (not _ref)
    assignment = Assignment.query.get(submission.assignment_id)
    document = Document.query.get(submission.document_id)

    if not document:
        flash('Document not found for this submission', 'danger')
        return redirect(url_for('student.view_assignments'))

    # Check blockchain verification manually instead of relying on a model attribute
    is_verified = False
    grade_verified = False

    # Try to verify document on blockchain
    try:
        blockchain = get_blockchain_service()
        if blockchain and document.hash:
            is_verified = blockchain.verify_document(document.hash)

            # Check grade verification
            if submission.status == 'graded' and document.nft_token_id:
                # Implement grade verification logic here if needed
                grade_verified = True
    except Exception as e:
        print(f"Blockchain verification error: {e}")

    return render_template(
        'student/view_submission.html',
        submission=submission,
        assignment=assignment,
        document=document,
        is_verified=is_verified,
        grade_verified=grade_verified if submission.status == 'graded' else None,
        user=user
    )
@student.route('/documents')
def view_documents():
    user = User.query.get(session['user_id'])
    documents = Document.query.filter_by(user_id=user.id).order_by(Document.uploaded_at.desc()).all()

    return render_template(
        'student/documents.html',
        documents=documents,
        user=user
    )

@student.route('/tokens')
def view_tokens():
    user = User.query.get(session['user_id'])

    # Get token balance and transactions
    token_balance = get_token_balance(user.id)
    transactions = get_user_transactions(user.id)

    return render_template(
        'student/tokens.html',
        user=user,
        token_balance=token_balance,
        transactions=transactions
    )

@student.route('/upload_document', methods=['GET', 'POST'])
def upload_document():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(url_for('student.documents'))

        file = request.files['file']
        document_name = request.form.get('document_name', file.filename)

        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('student.documents'))

        document = save_uploaded_file(
            file=file,
            document_type='general',
            user_id=user.id
        )

        if document:
            flash('Document uploaded and recorded on blockchain successfully!', 'success')
        else:
            flash('Error uploading document', 'danger')

        return redirect(url_for('student.view_documents'))

    return render_template('student/upload_document.html', user=user)

@student.route('/delete_document/<int:document_id>', methods=['POST'])
def delete_document(document_id):
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)

    # Check if user owns the document
    if document.user_id != user.id:
        flash('You do not have permission to delete this document', 'danger')
        return redirect(url_for('student.view_documents'))

    # Check if document is part of a submission
    submission = Submission.query.filter_by(document_id=document_id).first()
    if submission:
        flash('Cannot delete document as it is part of a submission', 'danger')
        return redirect(url_for('student.view_documents'))

    try:
        # Delete the file from storage
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete from database
        db.session.delete(document)
        db.session.commit()

        flash('Document deleted successfully', 'success')
    except Exception as e:
        print(f"Error deleting document: {str(e)}")
        flash('Error deleting document', 'danger')

    return redirect(url_for('student.view_documents'))

@student.route('/download_document/<int:document_id>')
def download_document(document_id):
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)

    # Check if user has permission to download
    if document.user_id != user.id:
        flash('You do not have permission to download this document', 'danger')
        return redirect(url_for('student.view_documents'))

    try:
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            document.filename,
            as_attachment=True,
            download_name=document.original_filename
        )
    except Exception as e:
        print(f"Error downloading document: {str(e)}")
        flash('Error downloading document', 'danger')
        return redirect(url_for('student.view_documents'))