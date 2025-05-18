<?php
// This file is part of Moodle - http://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle.  If not, see <http://www.gnu.org/licenses/>.

namespace local_blockchain;

defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir . '/filelib.php');

class blockchain_service {
    private $web3;
    private $token_contract;
    private $document_contract;
    private $wallet_factory_contract;
    private $token_tracker_contract;
    private $offline_mode;
    private $blockchain_enabled;

    public function __construct() {
        global $CFG;
        
        $this->offline_mode = true;
        $this->blockchain_enabled = false;

        // Check if blockchain is enabled in config
        if (!get_config('local_blockchain', 'enabled')) {
            return;
        }

        try {
            // Initialize Web3 connection
            $provider_url = get_config('local_blockchain', 'provider_url');
            if (empty($provider_url)) {
                return;
            }

            // Initialize Web3 connection using PHP Web3 library
            $this->web3 = new \Web3\Web3($provider_url);

            // Load contract ABIs
            $abis_path = $CFG->dirroot . '/local/blockchain/contracts/abis';
            
            // Initialize contracts
            $this->initialize_contracts($abis_path);

            $this->offline_mode = false;
            $this->blockchain_enabled = true;

        } catch (\Exception $e) {
            debugging('Blockchain service initialization error: ' . $e->getMessage());
        }
    }

    private function initialize_contracts($abis_path) {
        // Load contract ABIs and addresses
        $token_abi = file_get_contents($abis_path . '/token_abi.json');
        $document_abi = file_get_contents($abis_path . '/document_abi.json');
        $wallet_factory_abi = file_get_contents($abis_path . '/user_wallet_factory_abi.json');
        $token_tracker_abi = file_get_contents($abis_path . '/user_token_tracker_abi.json');

        $token_address = get_config('local_blockchain', 'token_contract_address');
        $document_address = get_config('local_blockchain', 'document_contract_address');
        $wallet_factory_address = get_config('local_blockchain', 'wallet_factory_address');
        $token_tracker_address = get_config('local_blockchain', 'token_tracker_address');

        // Initialize contract instances
        $this->token_contract = $this->web3->eth->contract($token_abi, $token_address);
        $this->document_contract = $this->web3->eth->contract($document_abi, $document_address);
        $this->wallet_factory_contract = $this->web3->eth->contract($wallet_factory_abi, $wallet_factory_address);
        $this->token_tracker_contract = $this->web3->eth->contract($token_tracker_abi, $token_tracker_address);
    }

    public function verify_document($fileid) {
        global $DB;

        if ($this->offline_mode) {
            return true; // Simulate verification in offline mode
        }

        try {
            $document = $DB->get_record('local_blockchain_documents', ['fileid' => $fileid]);
            if (!$document) {
                return false;
            }

            // Verify document on blockchain
            $result = $this->document_contract->call('verifyDocument', [$document->hash]);
            
            if ($result) {
                $document->is_verified = 1;
                $document->timemodified = time();
                $DB->update_record('local_blockchain_documents', $document);
            }

            return $result;
        } catch (\Exception $e) {
            debugging('Document verification error: ' . $e->getMessage());
            return false;
        }
    }

    public function mint_document_nft($fileid, $metadata) {
        global $DB, $USER;

        if ($this->offline_mode) {
            return true; // Simulate NFT minting in offline mode
        }

        try {
            $document = $DB->get_record('local_blockchain_documents', ['fileid' => $fileid]);
            if (!$document) {
                return false;
            }

            // Mint NFT on blockchain
            $tx_hash = $this->document_contract->send('mintDocument', [
                $document->hash,
                $metadata,
                false, // is_assignment
                0 // deadline
            ], ['from' => $USER->blockchain_address]);

            if ($tx_hash) {
                $document->blockchain_tx = $tx_hash;
                $document->timemodified = time();
                $DB->update_record('local_blockchain_documents', $document);
                return true;
            }

            return false;
        } catch (\Exception $e) {
            debugging('NFT minting error: ' . $e->getMessage());
            return false;
        }
    }

    public function award_tokens($userid, $amount, $reason) {
        global $DB;

        if ($this->offline_mode) {
            // Record transaction locally in offline mode
            $transaction = (object)[
                'userid' => $userid,
                'amount' => $amount,
                'transaction_type' => 'reward',
                'reason' => $reason,
                'timecreated' => time()
            ];
            return $DB->insert_record('local_blockchain_tokens', $transaction);
        }

        try {
            $user = $DB->get_record('user', ['id' => $userid]);
            if (!$user || !$user->blockchain_address) {
                return false;
            }

            // Award tokens on blockchain
            $tx_hash = $this->token_tracker_contract->send('earnTokens', [
                $user->blockchain_address,
                $amount,
                $reason
            ]);

            if ($tx_hash) {
                // Record transaction
                $transaction = (object)[
                    'userid' => $userid,
                    'amount' => $amount,
                    'transaction_type' => 'reward',
                    'reason' => $reason,
                    'blockchain_tx' => $tx_hash,
                    'timecreated' => time()
                ];
                return $DB->insert_record('local_blockchain_tokens', $transaction);
            }

            return false;
        } catch (\Exception $e) {
            debugging('Token award error: ' . $e->getMessage());
            return false;
        }
    }

    public function check_integrity($fileid) {
        global $DB;

        if ($this->offline_mode) {
            return true; // Simulate integrity check in offline mode
        }

        try {
            $document = $DB->get_record('local_blockchain_documents', ['fileid' => $fileid]);
            if (!$document) {
                return false;
            }

            // Check document integrity on blockchain
            $result = $this->document_contract->call('checkIntegrity', [$document->hash]);
            
            if (!$result) {
                // Record integrity violation
                $violation = (object)[
                    'userid' => $document->userid,
                    'original_document_id' => $document->id,
                    'violation_type' => 'duplicate',
                    'description' => 'Document hash matches existing document on blockchain',
                    'status' => 'pending',
                    'timecreated' => time(),
                    'timemodified' => time()
                ];
                $DB->insert_record('local_blockchain_integrity', $violation);
            }

            return $result;
        } catch (\Exception $e) {
            debugging('Integrity check error: ' . $e->getMessage());
            return false;
        }
    }

    public function get_token_balance($userid) {
        global $DB;

        if ($this->offline_mode) {
            // Calculate balance from local transactions
            $rewards = $DB->get_records_sql(
                "SELECT SUM(amount) as total FROM {local_blockchain_tokens} 
                 WHERE userid = ? AND transaction_type = 'reward'",
                [$userid]
            );
            $spends = $DB->get_records_sql(
                "SELECT SUM(amount) as total FROM {local_blockchain_tokens} 
                 WHERE userid = ? AND transaction_type = 'spend'",
                [$userid]
            );
            
            $total_rewards = $rewards ? $rewards[0]->total : 0;
            $total_spends = $spends ? $spends[0]->total : 0;
            
            return $total_rewards - $total_spends;
        }

        try {
            $user = $DB->get_record('user', ['id' => $userid]);
            if (!$user || !$user->blockchain_address) {
                return 0;
            }

            // Get balance from blockchain
            return $this->token_tracker_contract->call('getUserTokenBalance', [$user->blockchain_address]);
        } catch (\Exception $e) {
            debugging('Token balance check error: ' . $e->getMessage());
            return 0;
        }
    }

    public function is_connected() {
        return !$this->offline_mode && $this->blockchain_enabled;
    }
} 