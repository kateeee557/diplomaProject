from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_from_directory, current_app
from datetime import datetime
import os
from app import db
from models.user import User
from models.assignment import Assignment
from models.document import Document
from models.submission import Submission
from models.integrity_violation import IntegrityViolation
from services.document_service import save_uploaded_file, verify_document_on_blockchain
from services.grade_service import grade_submission as grade_service, verify_grade
from services.blockchain_service import get_blockchain_service
import logging

logger = logging.getLogger(__name__)

teacher = Blueprint('teacher', __name__)

@teacher.before_request
def check_teacher():
    # Ensure user is logged in and is a teacher
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Please log in as a teacher to access this page', 'warning')
        return redirect(url_for('auth.login'))

@teacher.route('/dashboard')
def dashboard():
    user = User.query.get(session['user_id'])

    # Get assignments created by this teacher
    assignments = Assignment.query.filter_by(teacher_id=user.id).all()

    # Add statistics to each assignment
    for assignment in assignments:
        assignment.submission_count = Submission.query.filter_by(assignment_id=assignment.id).count()
        # In a real app, get actual count of enrolled students
        assignment.student_count = User.query.filter_by(role='student').count()

    # Get pending submissions that need grading
    pending_submissions = Submission.query.join(Assignment).filter(
        Assignment.teacher_id == user.id,
        Submission.status == 'submitted'
    ).order_by(Submission.submitted_at.desc()).limit(10).all()

    # Get integrity violations for this teacher's assignments
    integrity_violations = IntegrityViolation.query.join(
        Document, IntegrityViolation.original_document_id == Document.id
    ).join(
        Submission, Document.id == Submission.document_id
    ).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        Assignment.teacher_id == user.id
    ).all()

    return render_template(
        'teacher/dashboard.html',
        user=user,
        assignments=assignments,
        pending_submissions=pending_submissions,
        integrity_violations=integrity_violations
    )

@teacher.route('/assignments')
def manage_assignments():
    user = User.query.get(session['user_id'])
    assignments = Assignment.query.filter_by(teacher_id=user.id).order_by(Assignment.deadline).all()

    # Add statistics to each assignment
    for assignment in assignments:
        assignment.submission_count = Submission.query.filter_by(assignment_id=assignment.id).count()
        # In a real app, get actual count of enrolled students
        assignment.student_count = User.query.filter_by(role='student').count()

        # Get on-time submission percentage
        on_time = Submission.query.filter(
            Submission.assignment_id == assignment.id,
            Submission.submitted_at <= assignment.deadline
        ).count()

        if assignment.submission_count > 0:
            assignment.on_time_percentage = int(on_time / assignment.submission_count * 100)
        else:
            assignment.on_time_percentage = 0

    return render_template(
        'teacher/assignments.html',
        assignments=assignments,
        user=user
    )

@teacher.route('/create_assignment', methods=['GET', 'POST'])
def create_assignment():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        deadline_str = request.form['deadline']

        # Parse datetime from form
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')

        new_assignment = Assignment(
            title=title,
            description=description,
            deadline=deadline,
            teacher_id=user.id
        )

        db.session.add(new_assignment)
        db.session.commit()

        flash('Assignment created successfully!', 'success')
        return redirect(url_for('teacher.manage_assignments'))

    return render_template('teacher/create_assignment.html', user=user)

@teacher.route('/edit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
def edit_assignment(assignment_id):
    user = User.query.get(session['user_id'])
    assignment = Assignment.query.get_or_404(assignment_id)

    # Check if teacher owns this assignment
    if assignment.teacher_id != user.id:
        flash('You do not have permission to edit this assignment', 'danger')
        return redirect(url_for('teacher.manage_assignments'))

    if request.method == 'POST':
        assignment.title = request.form['title']
        assignment.description = request.form['description']
        deadline_str = request.form['deadline']
        assignment.deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')

        db.session.commit()
        flash('Assignment updated successfully!', 'success')
        return redirect(url_for('teacher.manage_assignments'))

    return render_template('teacher/edit_assignment.html', assignment=assignment, user=user)
@teacher.route('/view_submission/<int:submission_id>')
def view_submission(submission_id):
    user = User.query.get(session['user_id'])
    submission = Submission.query.get_or_404(submission_id)

    # Get the assignment through the relationship
    assignment = submission.assignment

    # Check if teacher owns this assignment
    if assignment.teacher_id != user.id:
        flash('You do not have permission to view this submission', 'danger')
        return redirect(url_for('teacher.manage_assignments'))

    document = submission.document
    student = submission.student

    # No need to verify on blockchain every time - use stored values
    is_verified = document.is_blockchain_verified

    # Only verify grade if the submission is already graded
    grade_verified = submission.grade_verified if submission.status == 'graded' else None

    return render_template(
        'teacher/view_submission.html',
        submission=submission,
        assignment=assignment,
        document=document,
        student=student,
        is_verified=is_verified,
        grade_verified=grade_verified,
        user=user
    )

@teacher.route('/grade_submission/<int:submission_id>', methods=['GET', 'POST'])
def grade_submission(submission_id):
    """Grade a student submission"""
    print(f"Grading submission {submission_id}")  # Debug
    user = User.query.get(session['user_id'])
    submission = Submission.query.get_or_404(submission_id)
    assignment = submission.assignment_ref  # Using assignment_ref instead of assignment

    print(f"Found submission and assignment: {assignment.title}")  # Debug

    # Check if teacher owns this assignment
    if assignment.teacher_id != user.id:
        flash('You do not have permission to grade this submission', 'danger')
        return redirect(url_for('teacher.dashboard'))

    if request.method == 'POST':
        print("Processing POST request for grading")  # Debug
        print(f"Form data: {request.form}")  # Debug

        grade_value = request.form.get('grade')
        feedback = request.form.get('feedback')

        print(f"Grade: {grade_value}, Feedback: {feedback}")  # Debug

        # Basic validation
        if not grade_value or not feedback:
            flash('Both grade and feedback are required', 'warning')
            return redirect(url_for('teacher.grade_submission', submission_id=submission_id))

        try:
            # Call grade service to record the grade
            from services.grade_service import grade_submission as grade_service
            print("Calling grade_service")  # Debug
            success = grade_service(submission_id, grade_value, feedback, user.id)
            print(f"Grade service result: {success}")  # Debug

            if success:
                flash('Submission graded successfully!', 'success')
            else:
                flash('Error recording grade. Please try again.', 'danger')

            return redirect(url_for('teacher.view_submissions', assignment_id=assignment.id))
        except Exception as e:
            print(f"Exception in grade_submission: {str(e)}")  # Debug
            flash(f'Error grading submission: {str(e)}', 'danger')
            return redirect(url_for('teacher.grade_submission', submission_id=submission_id))

    # GET request - show grading form
    document = submission.document_ref  # Using document_ref instead of document
    student = submission.student

    print(f"Rendering grade form template")  # Debug
    return render_template(
        'teacher/grade_submission.html',
        submission=submission,
        assignment=assignment,
        student=student,
        document=document,
        user=user
    )

@teacher.route('/students')
def view_students():
    user = User.query.get(session['user_id'])
    students = User.query.filter_by(role='student').all()

    # Get submission counts for each student
    for student in students:
        student.submission_count = Submission.query.filter_by(student_id=student.id).count()
        student.graded_count = Submission.query.filter_by(
            student_id=student.id,
            status='graded'
        ).count()

    return render_template(
        'teacher/students.html',
        students=students,
        user=user
    )

@teacher.route('/documents')
def view_documents():
    user = User.query.get(session['user_id'])

    # Get documents uploaded by the teacher
    teacher_documents = Document.query.filter_by(
        user_id=user.id
    ).order_by(Document.uploaded_at.desc()).all()

    # Get teacher's assignments for the recent submissions section
    assignments = Assignment.query.filter_by(teacher_id=user.id).all()

    # Collect and sort recent submissions
    recent_submissions = []
    for assignment in assignments:
        for submission in assignment.submissions:  # This still works because it's defined in Assignment
            recent_submissions.append(submission)

    # Sort and limit to 5
    recent_submissions = sorted(
        recent_submissions,
        key=lambda x: x.submitted_at if hasattr(x, 'submitted_at') else datetime.now(),
        reverse=True
    )[:5]

    return render_template(
        'teacher/documents.html',
        documents=teacher_documents,
        assignments=assignments,
        recent_submissions=recent_submissions,
        user=user
    )

@teacher.route('/upload_document', methods=['GET', 'POST'])
def upload_document():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(url_for('teacher.view_documents'))

        file = request.files['file']
        document_name = request.form.get('document_name', file.filename)
        document_type = request.form.get('document_type', 'material')

        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('teacher.view_documents'))

        document = save_uploaded_file(
            file=file,
            document_type=document_type,
            user_id=user.id
        )

        if document:
            flash('Document uploaded and recorded on blockchain successfully!', 'success')
        else:
            flash('Error uploading document', 'danger')

        return redirect(url_for('teacher.view_documents'))

    return render_template('teacher/upload_document.html', user=user)

@teacher.route('/delete_document/<int:document_id>', methods=['POST'])
def delete_document(document_id):
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)

    # Check if user owns the document
    if document.user_id != user.id:
        flash('You do not have permission to delete this document', 'danger')
        return redirect(url_for('teacher.view_documents'))

    # Check if document is part of a submission
    submission = Submission.query.filter_by(document_id=document_id).first()
    if submission:
        flash('Cannot delete document as it is part of a submission', 'danger')
        return redirect(url_for('teacher.view_documents'))

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

    return redirect(url_for('teacher.view_documents'))

@teacher.route('/download_document/<int:document_id>')
def download_document(document_id):
    """Download a document file"""
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)

    # Check if user has permission to download
    # Teacher can download any document they uploaded OR any submission for their assignments
    has_permission = False

    # Check if teacher owns the document
    if document.user_id == user.id:
        has_permission = True

    # Check if document is part of a submission for teacher's assignment
    submission = Submission.query.filter_by(document_id=document_id).first()
    if submission and submission.assignment_ref.teacher_id == user.id:  # Changed from submission.assignment
        has_permission = True

    if not has_permission:
        flash('You do not have permission to download this document', 'danger')
        return redirect(url_for('teacher.dashboard'))

    try:
        file_path = document.file_path()  # This should return the full path to the file

        if not os.path.exists(file_path):
            flash('File not found on server', 'danger')
            return redirect(url_for('teacher.dashboard'))

        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path),
            as_attachment=True,
            download_name=document.original_filename
        )
    except Exception as e:
        print(f"Error downloading document: {str(e)}")
        flash(f'Error downloading document: {str(e)}', 'danger')
        return redirect(url_for('teacher.dashboard'))



# Ensure these functions are correctly indented within the file
@teacher.route('/integrity_violations')
def view_integrity_violations():
    user = User.query.get(session['user_id'])

    # Find all integrity violations for documents that belong to this teacher's assignments
    violations = IntegrityViolation.query.join(
        Document, IntegrityViolation.original_document_id == Document.id
    ).join(
        Submission, Document.id == Submission.document_id
    ).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        Assignment.teacher_id == user.id
    ).order_by(IntegrityViolation.attempted_at.desc()).all()

    return render_template(
        'teacher/integrity_violations.html',
        violations=violations,
        user=user
    )

@teacher.route('/review_violation/<int:violation_id>', methods=['POST'])
def review_violation(violation_id):
    user = User.query.get(session['user_id'])
    violation = IntegrityViolation.query.get_or_404(violation_id)

    # Check if this violation is for a document associated with this teacher's assignment
    original_doc = Document.query.get(violation.original_document_id)
    submission = Submission.query.filter_by(document_id=original_doc.id).first()

    if not submission or submission.assignment.teacher_id != user.id:
        flash('You do not have permission to review this violation', 'danger')
        return redirect(url_for('teacher.dashboard'))

    # Update the violation record
    violation.reviewed = True
    violation.notes = request.form.get('notes', '')

    db.session.commit()
    flash('Integrity violation marked as reviewed', 'success')

    return redirect(url_for('teacher.view_integrity_violations'))

@teacher.route('/view_submissions/<int:assignment_id>')
def view_submissions(assignment_id):
    user = User.query.get(session['user_id'])
    assignment = Assignment.query.get_or_404(assignment_id)

    # Check if teacher owns this assignment
    if assignment.teacher_id != user.id:
        flash('You do not have permission to view these submissions', 'danger')
        return redirect(url_for('teacher.manage_assignments'))

    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()

    # Get all students (in a real app, only get enrolled students)
    students = User.query.filter_by(role='student').all()

    # Create a dictionary of student_id -> submission
    submission_map = {s.student_id: s for s in submissions}

    # Create a list of students with submission status
    student_submissions = []
    for student in students:
        if student.id in submission_map:
            sub = submission_map[student.id]
            student_submissions.append({
                'student': student,
                'submission': sub,
                'status': sub.status,
                'on_time': sub.is_on_time(),
                'submitted_at': sub.submitted_at
            })
        else:
            student_submissions.append({
                'student': student,
                'submission': None,
                'status': 'not_submitted',
                'on_time': False,
                'submitted_at': None
            })

    return render_template(
        'teacher/view_submissions.html',
        assignment=assignment,
        student_submissions=student_submissions,
        user=user,
        now=datetime.utcnow()
    )