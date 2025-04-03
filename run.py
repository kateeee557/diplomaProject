import os
import logging
from flask_migrate import Migrate
from app import create_app, db
from models.user import User
from models.assignment import Assignment
from models.document import Document
from models.submission import Submission
from models.token import TokenTransaction

# Create the Flask app
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

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

# Initialize Flask-Migrate
migrate = Migrate(app, db)

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
        # Ensure uploads folder exists
        uploads_dir = app.config['UPLOAD_FOLDER']
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            logger.info(f"Created uploads directory: {uploads_dir}")

        # Ensure blockchain directories exist
        blockchain_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blockchain')
        if not os.path.exists(blockchain_dir):
            os.makedirs(blockchain_dir)
            logger.info(f"Created blockchain directory: {blockchain_dir}")

        abis_dir = os.path.join(blockchain_dir, 'abis')
        if not os.path.exists(abis_dir):
            os.makedirs(abis_dir)
            logger.info(f"Created abis directory: {abis_dir}")

        contracts_dir = os.path.join(blockchain_dir, 'contracts')
        if not os.path.exists(contracts_dir):
            os.makedirs(contracts_dir)
            logger.info(f"Created contracts directory: {contracts_dir}")

        # Check if blockchain provider is configured and deploy contracts if needed
        if app.config.get('BLOCKCHAIN_PROVIDER'):
            try:
                logger.info("Checking for deployed blockchain contracts...")
                from blockchain.deploy_contracts import deploy_contracts

                # Deploy contracts
                addresses = deploy_contracts()

                # Update app config with new addresses
                if addresses:
                    app.config['TOKEN_CONTRACT_ADDRESS'] = addresses.get('token_contract', app.config['TOKEN_CONTRACT_ADDRESS'])
                    app.config['DOCUMENT_CONTRACT_ADDRESS'] = addresses.get('document_contract', app.config['DOCUMENT_CONTRACT_ADDRESS'])
                    app.config['USER_WALLET_FACTORY_ADDRESS'] = addresses.get('wallet_factory_contract', app.config['USER_WALLET_FACTORY_ADDRESS'])
                    app.config['USER_TOKEN_TRACKER_ADDRESS'] = addresses.get('token_tracker_contract', app.config['USER_TOKEN_TRACKER_ADDRESS'])
                    logger.info("Application config updated with deployed contract addresses")

                # Initialize blockchain service
                from services.blockchain_service import get_blockchain_service
                blockchain = get_blockchain_service()
                logger.info("Blockchain service initialized successfully")
            except Exception as e:
                logger.error(f"Error during blockchain setup: {e}")
                logger.warning("Application will continue without blockchain integration")
        else:
            logger.warning("No blockchain provider configured - blockchain features will be disabled")
    except Exception as e:
        logger.error(f"Error during application setup: {e}")

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

                # Create test student
                student = User(
                    name='Test Student',
                    email='student@academicblockchain.com',
                    role='student'
                )
                student.set_password('studentpassword')
                db.session.add(student)

                db.session.commit()
                logger.info("Test users created")
        except Exception as e:
            logger.error(f"Error creating test data: {e}")
            db.session.rollback()

# In the run_database_migrations function or similar:
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