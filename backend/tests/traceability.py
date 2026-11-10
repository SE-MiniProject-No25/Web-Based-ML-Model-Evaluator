"""Which automated tests cover which Test Plan case (Test Plan section 8). Used by scripts/tc_report.py.

A test id is ``tests/<file>.py::<test function>``; parametrised variants all count. Cases that are not
(fully) automated are listed in ``NOT_AUTOMATED`` with the reason, so the Test Report can say so.
"""

AUTOMATED = {
    "TC-01": ["tests/test_api_submit.py::test_valid_classification_submission_is_accepted_with_an_id"],
    "TC-02": [
        "tests/test_api_submit.py::test_valid_classification_submission_is_accepted_with_an_id",
        "tests/test_api_submit.py::test_valid_regression_submission_is_accepted",
    ],
    "TC-03": ["tests/test_api_submit.py::test_unsupported_file_type_is_rejected_and_creates_nothing"],
    "TC-04": [
        "tests/test_api_submit.py::test_model_exactly_at_size_limit_is_accepted",
        "tests/test_api_submit.py::test_model_one_byte_over_size_limit_is_rejected",
        "tests/test_api_submit.py::test_dataset_exactly_at_size_limit_is_accepted",
        "tests/test_api_submit.py::test_dataset_one_byte_over_size_limit_is_rejected",
        "tests/test_api_submit.py::test_enforce_file_size_stops_early_without_reading_entire_file",
    ],
    "TC-05": [
        "tests/test_api_submit.py::test_target_column_not_in_dataset_is_rejected",
        "tests/test_api_submit.py::test_valid_target_column_in_dataset_is_accepted",
    ],
    "TC-06": ["tests/test_api_submit.py::test_invalid_task_type_is_rejected"],
    "TC-07": ["tests/test_api_submit.py::test_missing_field_is_rejected_and_creates_nothing"],
    "TC-08": [
        "tests/test_acceptance.py::test_classification_reference_pair_reports_the_expected_metrics",
        "tests/test_metrics_service.py::test_classification_metrics_match_en02_reference_fixture",
    ],
    "TC-09": [
        "tests/test_acceptance.py::test_regression_reference_pair_reports_the_expected_metrics",
        "tests/test_metrics_service.py::test_regression_metrics_match_en02_reference_fixture",
    ],
    "TC-10": [
        "tests/test_api_status.py::test_status_follows_the_lifecycle_to_completed",
        "tests/test_api_status.py::test_end_to_end_submit_then_read_the_result",
    ],
    "TC-11": [
        "tests/test_evaluation_limits.py::test_feature_mismatch_ends_as_incompatible_inputs",
        "tests/test_evaluation_limits.py::test_api_reports_incompatible_inputs_to_the_client",
        "tests/test_api_status.py::test_end_to_end_incompatible_inputs_end_failed_without_leaking_details",
    ],
    "TC-12": [
        "tests/test_api_download.py::test_completed_evaluation_downloads_as_a_json_attachment",
        "tests/test_api_download.py::test_downloaded_metrics_match_the_reference_values",
    ],
    "TC-13": [
        "tests/test_api_submit.py::test_client_filenames_never_reach_the_filesystem",
        "tests/test_storage.py::test_user_controlled_extensions_cannot_alter_the_path",
        "tests/test_storage.py::test_delete_removes_stored_file_but_not_outside_files",
    ],
    "TC-14": ["tests/test_api_submit.py::test_malformed_model_is_rejected"],
    "TC-15": [
        "tests/test_evaluation_limits.py::test_exceeding_the_time_limit_stops_the_evaluation",
        "tests/test_evaluation_limits.py::test_api_stops_an_evaluation_that_exceeds_the_time_limit",
        "tests/test_evaluation_limits.py::test_exceeding_the_memory_limit_stops_the_evaluation",
    ],
    "TC-16": [
        "tests/test_api_submit.py::test_error_responses_use_the_standard_format_without_internal_details",
        "tests/test_evaluation_limits.py::test_a_crashing_model_fails_with_a_generic_message_and_logs_the_traceback",
        "tests/test_api_status.py::test_end_to_end_incompatible_inputs_end_failed_without_leaking_details",
        "tests/test_errors.py::test_tc16_server_validation_error_leaks_no_trace_or_path",
        "tests/test_errors.py::test_tc16_runtime_evaluation_error_leaks_no_trace_or_path",
    ],
    "TC-17": [
        "tests/test_auth.py::test_missing_credentials_rejected_with_401",
        "tests/test_auth.py::test_invalid_and_missing_credentials_return_401_for_both_get_and_post",
        "tests/test_auth.py::test_valid_x_api_key_header_post",
        "tests/test_auth.py::test_valid_authorization_bearer_header_post",
        "tests/test_auth.py::test_fail_secure_when_auth_enabled_but_no_key_configured",
        "tests/test_auth.py::test_download_endpoint_is_protected_and_works_with_credentials",
        "tests/test_auth.py::test_health_endpoint_remains_unauthenticated_when_auth_enabled",
    ],
    "TC-18": [
        "tests/test_storage.py::test_cleanup_expired_deletes_files_older_than_retention_period",
        "tests/test_storage.py::test_cleanup_expired_boundary_exact_limit",
        "tests/test_storage.py::test_cleanup_expired_never_deletes_active_paths_even_if_expired",
        "tests/test_storage.py::test_api_background_retention_cleanup_e2e",
        "tests/test_retention.py::test_the_sweep_keeps_the_files_of_a_running_evaluation_and_removes_finished_ones",
        "tests/test_retention.py::test_expired_files_are_removed_at_start_up_without_any_request",
        "tests/test_retention.py::test_expired_files_are_removed_on_a_timer_without_any_request",
    ],
    "TC-19": ["tests/test_ack_time.py::test_ten_valid_requests_are_each_acknowledged_within_two_seconds"],
    "TC-20": ["tests/test_determinism.py::test_repeated_evaluations_produce_identical_metrics"],
    "TC-22": [
        "tests/test_result_service.py::test_create_stores_a_pending_record_with_a_random_uuid",
        "tests/test_result_service.py::test_ids_are_unique",
        "tests/test_result_service.py::test_a_terminal_status_never_changes",
        "tests/test_api_submit.py::test_each_submission_gets_a_different_id",
    ],
    "TC-23": ["tests/test_api_submit.py::test_malformed_csv_is_rejected"],
    "TC-24": [
        "tests/test_api_status.py::test_unknown_id_is_a_404_with_the_standard_error",
        "tests/test_api_download.py::test_unknown_id_is_a_404",
    ],
    "TC-25": [
        "tests/test_api_download.py::test_download_before_completion_is_a_409_with_no_file",
        "tests/test_api_download.py::test_failed_evaluation_has_nothing_to_download",
    ],
}

NOT_AUTOMATED = {
    "TC-21": "Manual usability test with a fresh user (US-22); see deliverable-1/usability-testing/.",
}
