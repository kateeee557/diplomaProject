import os
import logging
from flask_migrate import Migrate
from app import create_app, db
from models.user import User
from models.assignment import Assignment
from models.document import Document
from models.submission import Submission
from models.token import TokenTransaction
from services.blockchain_service import get_blockchain_service

# Create the Flask app
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('academic_blockchain.log')
    ]
)
logger = logging.getLogger(__name__)

@app.shell_context_processor
def make_shell_context():
    """Provide context for Flask shell"""
    return {
        'app': app,
        'db': db,
        'User': User,
        'Assignment': Assignment,
        'Document': Document,
        'Submission': Submission,
        'TokenTransaction': TokenTransaction
    }

@app.before_first_request
def setup_blockchain():
    """Initialize blockchain setup before first request"""
    try:
        # Attempt to initialize blockchain service
        blockchain = get_blockchain_service()
        logger.info("Blockchain service initialized successfully")
    except Exception as e:
        logger.error(f"Blockchain initialization failed: {e}")

def create_test_data():
    """
    Create initial test data for development
    Only run this in development environment
    """
    if app.config['ENV'] == 'development':
        try:
            # Check if database is empty
            if User.query.count() == 0:
                # Create test admin
                admin = User(
                    name='Admin User',
                    email='admin@academicblockchain.com',
                    role='teacher'
                )
                admin.set_password('adminpassword')
                db.session.add(admin)
                db.session.commit()
                logger.info("Test admin user created")
        except Exception as e:
            logger.error(f"Error creating test data: {e}")
            db.session.rollback()

def run_database_migrations():
    """
    Run database migrations
    """
    try:
        with app.app_context():
            # Create all tables that haven't been created yet
            db.create_all()
            logger.info("Database tables created/updated")
    except Exception as e:
        logger.error(f"Database migration error: {e}")

if __name__ == '__main__':
    # Ensure database is set up
    run_database_migrations()

    # Create test data in development
    create_test_data()

    # Run the application
    app.run(
        host='0.0.0.0',  # Listen on all available interfaces
        port=5000,
        debug=app.config['DEBUG']
    )