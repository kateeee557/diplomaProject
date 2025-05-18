# Academic Blockchain Plugin for Moodle

This plugin integrates blockchain technology into Moodle to enhance academic integrity, document verification, and implement a token-based reward system.

## Features

- 🔒 Blockchain-verified document submissions
- 🏆 Token-based reward system for academic achievements
- 📄 NFT minting for academic documents
- 🔐 Academic integrity violation detection
- 💰 Token economy for student rewards

## Prerequisites

1. Moodle installation (version 4.0 or higher)
2. PHP 7.4 or higher
3. Composer (for PHP dependencies)
4. Ethereum node (e.g., Ganache for development)
5. Web3.php library

## Installation

### 1. Install Dependencies

```bash
# Navigate to your Moodle root directory
cd /path/to/moodle

# Install Web3.php using Composer
composer require web3p/web3.php
```

### 2. Install the Plugin

1. Copy the entire `blockchain` directory to your Moodle's `local` directory:
   ```bash
   cp -r blockchain /path/to/moodle/local/
   ```

2. Log in to your Moodle site as an administrator

3. Navigate to Site Administration > Notifications
   - Moodle will detect the new plugin and install it
   - The database tables will be created automatically

### 3. Configure Smart Contracts

1. Deploy the smart contracts to your Ethereum network:
   - AcademicToken.sol
   - DocumentNFT.sol
   - UserWalletFactory.sol
   - TokenTracker.sol

2. Note down the deployed contract addresses

### 4. Plugin Configuration

1. Go to Site Administration > Plugins > Local plugins > Academic Blockchain

2. Configure the following settings:
   - Enable blockchain integration
   - Set blockchain provider URL (e.g., http://localhost:7545 for Ganache)
   - Enter contract addresses:
     - Token contract address
     - Document contract address
     - Wallet factory address
     - Token tracker address
   - Configure token rewards:
     - Submission reward amount
     - Grade reward multiplier

## Usage

### For Administrators

1. **Enable/Disable Features**
   - Navigate to Site Administration > Plugins > Local plugins > Academic Blockchain
   - Toggle blockchain features as needed
   - Configure reward amounts and multipliers

2. **Monitor Blockchain Status**
   - View blockchain connection status
   - Monitor contract interactions
   - Check system logs for blockchain operations

### For Teachers

1. **Assignment Management**
   - Create assignments as usual
   - The plugin automatically:
     - Verifies submissions on blockchain
     - Awards tokens for on-time submissions
     - Checks for academic integrity violations

2. **Grading**
   - Grade assignments normally
   - The plugin automatically:
     - Awards additional tokens based on grades
     - Records grades on blockchain
     - Updates student token balances

3. **Document Verification**
   - Upload teaching materials
   - Documents are automatically:
     - Hashed and stored on blockchain
     - Minted as NFTs
     - Verified for integrity

### For Students

1. **Submissions**
   - Submit assignments normally
   - Receive automatic:
     - Document verification
     - Token rewards for on-time submission
     - Additional tokens for good grades

2. **Token Management**
   - View token balance
   - Track token transactions
   - Use tokens for:
     - Extended deadlines
     - Special privileges
     - Academic achievements

## Development Mode

The plugin supports offline/development mode:

1. Enable development mode in settings
2. Features will be simulated without actual blockchain interaction
3. Useful for testing and development

## Troubleshooting

### Common Issues

1. **Blockchain Connection Failed**
   - Check provider URL
   - Verify Ethereum node is running
   - Check network connectivity

2. **Contract Interaction Errors**
   - Verify contract addresses
   - Check contract ABIs
   - Ensure sufficient gas

3. **Token Transaction Failures**
   - Check user wallet balance
   - Verify transaction permissions
   - Check gas limits

### Logs

- Check `academic_blockchain.log` for detailed error information
- Enable debug mode in Moodle for more verbose logging

## Security Considerations

1. **Private Keys**
   - Never store private keys in the database
   - Use secure key management
   - Implement proper access controls

2. **Smart Contracts**
   - Audit contracts before deployment
   - Use secure contract patterns
   - Implement proper access controls

3. **User Data**
   - Encrypt sensitive data
   - Implement proper access controls
   - Follow data protection regulations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This plugin is licensed under the GNU GPL v3 or later.

## Support

For support:
1. Check the documentation
2. Submit issues on GitHub
3. Contact the development team

## Version History

- 1.0.0 (2024-03-15)
  - Initial release
  - Basic blockchain integration
  - Token reward system
  - Document verification
  - Academic integrity checks 