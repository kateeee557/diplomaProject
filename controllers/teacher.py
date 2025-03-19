from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_from_directory
from flask_login import login_required, current_user  # Correct Flask-Login import
from datetime import datetime
import os
from app import db
from models.user import User
from models.assignment import Assignment
from models.document import Document
from models.submission import Submission
from services.document_service import save_uploaded_file, verify_document_on_blockchain
from services.grade_service import grade_submission, verify_grade

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

    return render_template(
        'teacher/dashboard.html',
        user=user,
        assignments=assignments,
        pending_submissions=pending_submissions
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

@teacher.route('/grade_submission/<int:submission_id>', methods=['GET', 'POST'])
def grade_submission(submission_id):
    user = User.query.get(session['user_id'])
    submission = Submission.query.get_or_404(submission_id)
    assignment = Assignment.query.get(submission.assignment_id)

    # Check if teacher owns this assignment
    if assignment.teacher_id != user.id:
        flash('You do not have permission to grade this submission', 'danger')
        return redirect(url_for('teacher.manage_assignments'))

    if request.method == 'POST':
        grade_value = request.form['grade']
        feedback = request.form['feedback']

        # Record grade
        success = grade_submission(submission_id, grade_value, feedback, user.id)

        if success:
            flash('Submission graded successfully and recorded on blockchain!', 'success')
        else:
            flash('Error recording grade on blockchain', 'danger')

        return redirect(url_for('teacher.view_submissions', assignment_id=submission.assignment_id))

    # GET request - show grading form
    student = User.query.get(submission.student_id)
    document = Document.query.get(submission.document_id)

    return render_template(
        'teacher/grade_submission.html',
        submission=submission,
        assignment=assignment,
        student=student,
        document=document,
        user=user
    )

@teacher.route('/view_submission/<int:submission_id>')
def view_submission(submission_id):
    user = User.query.get(session['user_id'])
    submission = Submission.query.get_or_404(submission_id)
    assignment = Assignment.query.get(submission.assignment_id)

    # Check if teacher owns this assignment
    if assignment.teacher_id != user.id:
        flash('You do not have permission to view this submission', 'danger')
        return redirect(url_for('teacher.manage_assignments'))

    document = Document.query.get(submission.document_id)
    student = User.query.get(submission.student_id)

    # Verify document and grade on blockchain
    is_verified = verify_document_on_blockchain(document.id)
    grade_verified = verify_grade(submission.id) if submission.status == 'graded' else None

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
        if hasattr(assignment, 'submissions'):
            for submission in assignment.submissions:
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
            return redirect(url_for('teacher.view_documents'))  # Changed from 'teacher.documents'

        file = request.files['file']
        document_name = request.form.get('document_name', file.filename)
        document_type = request.form.get('document_type', 'material')

        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('teacher.view_documents'))  # Changed from 'teacher.documents'

        document = save_uploaded_file(
            file=file,
            document_type=document_type,
            user_id=user.id
        )

        if document:
            flash('Document uploaded and recorded on blockchain successfully!', 'success')
        else:
            flash('Error uploading document', 'danger')

        return redirect(url_for('teacher.view_documents'))  # Changed from 'teacher.documents'

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
    user = User.query.get(session['user_id'])
    document = Document.query.get_or_404(document_id)

    # Check if user has permission to download
    if document.user_id != user.id:
        submission = Submission.query.filter_by(document_id=document_id).first()
        if not submission or submission.assignment.teacher_id != user.id:
            flash('You do not have permission to download this document', 'danger')
            return redirect(url_for('teacher.view_documents'))

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
        return redirect(url_for('teacher.view_documents'))

