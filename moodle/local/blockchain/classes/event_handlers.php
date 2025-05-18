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

class event_handlers {
    /**
     * Handle assignment submission event
     */
    public static function handle_assignment_submitted($event) {
        global $DB;

        // Get the blockchain service
        $blockchain = new blockchain_service();
        if (!$blockchain->is_connected()) {
            return;
        }

        // Get submission data
        $submission = $event->get_record_snapshot('assign_submission', $event->objectid);
        $assignment = $event->get_record_snapshot('assign', $submission->assignment);
        $user = $event->get_record_snapshot('user', $event->relateduserid);

        // Check if submission is on time
        $is_ontime = $submission->timemodified <= $assignment->duedate;

        if ($is_ontime) {
            // Award tokens for on-time submission
            $reward_amount = get_config('local_blockchain', 'submission_reward');
            $blockchain->award_tokens($user->id, $reward_amount, 'On-time submission');
        }

        // Verify document on blockchain
        if ($submission->fileid) {
            $blockchain->verify_document($submission->fileid);
            $blockchain->check_integrity($submission->fileid);
        }
    }

    /**
     * Handle assignment graded event
     */
    public static function handle_assignment_graded($event) {
        global $DB;

        // Get the blockchain service
        $blockchain = new blockchain_service();
        if (!$blockchain->is_connected()) {
            return;
        }

        // Get grade data
        $grade = $event->get_record_snapshot('assign_grades', $event->objectid);
        $assignment = $event->get_record_snapshot('assign', $grade->assignment);
        $user = $event->get_record_snapshot('user', $grade->userid);

        // Calculate grade-based reward
        $grade_percentage = ($grade->grade / $assignment->grade) * 100;
        $multiplier = get_config('local_blockchain', 'grade_reward_multiplier');
        $reward_amount = $grade_percentage * $multiplier;

        // Award tokens based on grade
        $blockchain->award_tokens($user->id, $reward_amount, 'Grade reward');
    }

    /**
     * Handle file uploaded event
     */
    public static function handle_file_uploaded($event) {
        global $DB;

        // Get the blockchain service
        $blockchain = new blockchain_service();
        if (!$blockchain->is_connected()) {
            return;
        }

        // Get file data
        $file = $event->get_record_snapshot('files', $event->objectid);
        
        // Calculate file hash
        $hash = hash_file('sha256', $file->filepath);

        // Store document in blockchain table
        $document = (object)[
            'userid' => $event->userid,
            'fileid' => $file->id,
            'hash' => $hash,
            'timecreated' => time(),
            'timemodified' => time()
        ];
        $DB->insert_record('local_blockchain_documents', $document);

        // Verify document on blockchain
        $blockchain->verify_document($file->id);
        $blockchain->check_integrity($file->id);
    }

    /**
     * Handle user created event
     */
    public static function handle_user_created($event) {
        global $DB;

        // Get the blockchain service
        $blockchain = new blockchain_service();
        if (!$blockchain->is_connected()) {
            return;
        }

        // Get user data
        $user = $event->get_record_snapshot('user', $event->objectid);

        // Create blockchain wallet for user
        $wallet_address = $blockchain->create_user_wallet($user->id);
        if ($wallet_address) {
            $user->blockchain_address = $wallet_address;
            $DB->update_record('user', $user);
        }
    }
} 