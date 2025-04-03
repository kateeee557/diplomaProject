# Academic Blockchain Platform

## Overview
Academic Blockchain is an innovative digital platform that leverages blockchain technology to enhance transparency, integrity, and accountability in academic processes. By utilizing blockchain and NFT technologies, the platform provides a secure and immutable system for document management, assignment submissions, and academic rewards.

## Key Features
- 🔒 Blockchain-Verified Documents
- 🏆 Token-Based Reward System
- 📄 Immutable Assignment Submissions
- 🔐 Academic Integrity Protection
- 📊 Transparent Grading Mechanism

## Technology Stack
- **Backend**: Python (Flask)
- **Blockchain**: Ethereum-based Smart Contracts (Solidity)
- **Frontend**: Bootstrap, HTML/CSS
- **Database**: SQLAlchemy
- **Blockchain Interaction**: Web3.py

## Installation Requirements
### Prerequisites
- Python 3.8+
- Ganache (Local Blockchain)
- pip (Python Package Manager)
- Node.js (for frontend dependencies)

### Setup Steps
1. Clone the repository
```bash
git clone https://github.com/yourusername/academic-blockchain.git
cd academic-blockchain
```

2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Initialize the project
```bash
python setup.py
```

5. Start the application
```bash
python run.py
```

## Blockchain Components
- **AcademicToken**: ERC20 token for rewards
- **DocumentNFT**: ERC721 token for document verification
- **UserAddressFactory**: Manages user blockchain wallets
- **UserTokenTracker**: Tracks token earnings and spending

## User Roles
### Student
- Register and create profile
- Submit assignments before deadlines
- Upload personal documents
- Earn academic tokens
- View grades and submission history

### Teacher
- Create and manage assignments
- Grade student submissions
- Upload teaching materials
- Monitor academic integrity
- View student performance

## Token Economy
- **Reward Mechanism**:
  - 10 tokens for on-time assignment submission
  - Additional tokens for high-performance grades
- **Token Benefits**:
  - Extended assignment deadlines
  - Academic achievement certificates
  - Priority registration
  - Special academic recognitions

## Security Features
- Immutable document storage via NFTs
- Blockchain-verified submissions
- Academic integrity violation detection
- Secure user authentication

## Test Accounts
- **Teacher**:
  - Email: teacher@example.com
  - Password: teacher123

- **Student1**:
  - Email: student1@example.com
  - Password: student123

 - **Student2**:
   - Email: student1@example.com
   - Password: student456


## Development Notes
- Runs in offline mode by default
- Blockchain features can be enabled/disabled in config
- Supports local and production environments

## Blockchain Status
The platform provides real-time blockchain connection status, allowing users to understand the current state of blockchain integration.

## Contribution
Contributions are welcome! Please read the contribution guidelines before submitting pull requests.


## Disclaimer
This is an experimental academic project demonstrating blockchain technology in educational contexts.