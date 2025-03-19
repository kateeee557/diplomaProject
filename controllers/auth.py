from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models.user import User
from web3 import Web3
from services.blockchain_service import get_blockchain_service
from services.token_service import record_token_reward
import logging

auth = Blueprint('auth', __name__)

@auth.route('/')
def index():
    # If user is not logged in, redirect to login
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # If user is logged in, redirect based on their role
    if session.get('role') == 'student':
        return redirect(url_for('student.dashboard'))
    elif session.get('role') == 'teacher':
        return redirect(url_for('teacher.dashboard'))

    # Fallback to login if no role is set
    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if user and user.check_password(password):
            # Save user info in session
            session['user_id'] = user.id
            session['name'] = user.name
            session['role'] = user.role

            # Update last login time
            user.last_login = db.func.now()
            db.session.commit()

            flash('Login successful!', 'success')
            return redirect(url_for('auth.index'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('auth/login.html')

@auth.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))

        try:
            # Generate an Ethereum address for the user
            w3 = Web3()
            account = w3.eth.account.create()

            # Create new user with blockchain address
            new_user = User(
                name=name,
                email=email,
                role=role,
                blockchain_address=account.address
            )

            # Set password
            new_user.set_password(password)

            # Save user to database
            db.session.add(new_user)
            db.session.commit()

            # Create user wallet on blockchain
            try:
                blockchain = get_blockchain_service()
                if blockchain.is_connected():
                    blockchain.create_user_wallet(new_user.blockchain_address)
                else:
                    logging.warning("Blockchain not connected, skipping wallet creation")
            except Exception as wallet_error:
                logging.error(f"Blockchain wallet creation failed: {wallet_error}")
                flash(f'Blockchain wallet creation failed, but your account was created', 'warning')

            # Award initial tokens
            try:
                record_token_reward(
                    new_user.id,
                    10,  # Initial token reward
                    "New user registration"
                )
            except Exception as token_error:
                logging.error(f"Initial token reward failed: {token_error}")
                flash(f'Initial token reward failed, but your account was created', 'warning')

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration failed: {e}")
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')