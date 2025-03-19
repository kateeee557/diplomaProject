const AcademicToken = artifacts.require("AcademicToken");
const DocumentNFT = artifacts.require("DocumentNFT");
const UserAddressFactory = artifacts.require("UserAddressFactory");
const UserTokenTracker = artifacts.require("UserTokenTracker");

// Configuration
const fs = require('fs');
const path = require('path');

module.exports = async function(deployer, network, accounts) {
    const deployAccount = accounts[0];
    console.log(`Deploying contracts from account: ${deployAccount}`);

    try {
        // Deploy AcademicToken first
        await deployer.deploy(AcademicToken, { from: deployAccount });
        const academicToken = await AcademicToken.deployed();
        console.log(`AcademicToken deployed at: ${academicToken.address}`);

        // Deploy DocumentNFT with AcademicToken address
        await deployer.deploy(DocumentNFT, academicToken.address, { from: deployAccount });
        const documentNFT = await DocumentNFT.deployed();
        console.log(`DocumentNFT deployed at: ${documentNFT.address}`);

        // Deploy UserAddressFactory
        await deployer.deploy(UserAddressFactory, { from: deployAccount });
        const userAddressFactory = await UserAddressFactory.deployed();
        console.log(`UserAddressFactory deployed at: ${userAddressFactory.address}`);

        // Deploy UserTokenTracker
        await deployer.deploy(UserTokenTracker, { from: deployAccount });
        const userTokenTracker = await UserTokenTracker.deployed();
        console.log(`UserTokenTracker deployed at: ${userTokenTracker.address}`);

        // Save contract addresses to a file
        const contractAddresses = {
            AcademicToken: academicToken.address,
            DocumentNFT: documentNFT.address,
            UserAddressFactory: userAddressFactory.address,
            UserTokenTracker: userTokenTracker.address
        };

        fs.writeFileSync(
            path.join(__dirname, '../deployed_addresses.json'),
            JSON.stringify(contractAddresses, null, 2)
        );
        console.log('Contract addresses saved to deployed_addresses.json');

        // Output for updating config.py
        console.log('\nCopy these settings to your config.py:');
        console.log(`TOKEN_CONTRACT_ADDRESS = '${academicToken.address}'`);
        console.log(`DOCUMENT_CONTRACT_ADDRESS = '${documentNFT.address}'`);
        console.log(`USER_WALLET_FACTORY_ADDRESS = '${userAddressFactory.address}'`);
        console.log(`USER_TOKEN_TRACKER_ADDRESS = '${userTokenTracker.address}'`);

    } catch (error) {
        console.error('Deployment error:', error);
        throw error;
    }
};