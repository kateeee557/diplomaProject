module.exports = {
    networks: {
        development: {
            host: "ganache",     // Docker service name for Ganache
            port: 7545,          // Default Ganache port
            network_id: "*",     // Match any network id
            gas: 6000000,        // Gas limit
            gasPrice: 20000000000
        },
        local: {
            host: "127.0.0.1",   // For using with local Ganache
            port: 7545,          // Default Ganache port
            network_id: "*",     // Match any network id
            gas: 6000000,        // Gas limit
            gasPrice: 20000000000
        }
    },
    compilers: {
        solc: {
            version: "0.8.17",   // Specify compiler version
            settings: {
                optimizer: {
                    enabled: true,   // Enable optimizer for gas savings
                    runs: 200        // Optimize for average use
                }
            }
        }
    },
    // Directory structure for contract artifacts
    contracts_directory: "./contracts",
    contracts_build_directory: "./abis",
    migrations_directory: "./migrations"
};