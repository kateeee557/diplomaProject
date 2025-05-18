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

defined('MOODLE_INTERNAL') || die();

if ($hassiteconfig) {
    $settings = new admin_settingpage('local_blockchain', get_string('pluginname', 'local_blockchain'));
    $ADMIN->add('localplugins', $settings);

    // Enable/Disable blockchain
    $settings->add(new admin_setting_configcheckbox(
        'local_blockchain/enabled',
        get_string('setting_enabled', 'local_blockchain'),
        get_string('setting_enabled_desc', 'local_blockchain'),
        0
    ));

    // Blockchain provider URL
    $settings->add(new admin_setting_configtext(
        'local_blockchain/provider_url',
        get_string('setting_provider_url', 'local_blockchain'),
        get_string('setting_provider_url_desc', 'local_blockchain'),
        'http://localhost:7545',
        PARAM_URL
    ));

    // Contract addresses
    $settings->add(new admin_setting_configtext(
        'local_blockchain/token_contract_address',
        get_string('setting_token_contract', 'local_blockchain'),
        get_string('setting_token_contract_desc', 'local_blockchain'),
        '',
        PARAM_TEXT
    ));

    $settings->add(new admin_setting_configtext(
        'local_blockchain/document_contract_address',
        get_string('setting_document_contract', 'local_blockchain'),
        get_string('setting_document_contract_desc', 'local_blockchain'),
        '',
        PARAM_TEXT
    ));

    $settings->add(new admin_setting_configtext(
        'local_blockchain/wallet_factory_address',
        get_string('setting_wallet_factory', 'local_blockchain'),
        get_string('setting_wallet_factory_desc', 'local_blockchain'),
        '',
        PARAM_TEXT
    ));

    $settings->add(new admin_setting_configtext(
        'local_blockchain/token_tracker_address',
        get_string('setting_token_tracker', 'local_blockchain'),
        get_string('setting_token_tracker_desc', 'local_blockchain'),
        '',
        PARAM_TEXT
    ));

    // Token reward settings
    $settings->add(new admin_setting_configtext(
        'local_blockchain/submission_reward',
        get_string('setting_submission_reward', 'local_blockchain'),
        get_string('setting_submission_reward_desc', 'local_blockchain'),
        '10',
        PARAM_FLOAT
    ));

    $settings->add(new admin_setting_configtext(
        'local_blockchain/grade_reward_multiplier',
        get_string('setting_grade_reward_multiplier', 'local_blockchain'),
        get_string('setting_grade_reward_multiplier_desc', 'local_blockchain'),
        '0.5',
        PARAM_FLOAT
    ));
} 