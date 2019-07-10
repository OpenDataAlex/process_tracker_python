SET search_path TO process_tracker;

INSERT INTO process_tracker.extract_status_lkup (extract_status_id, extract_status_name) VALUES (default, 'initializing');
INSERT INTO process_tracker.extract_status_lkup (extract_status_id, extract_status_name) VALUES (default, 'ready');
INSERT INTO process_tracker.extract_status_lkup (extract_status_id, extract_status_name) VALUES (default, 'loading');
INSERT INTO process_tracker.extract_status_lkup (extract_status_id, extract_status_name) VALUES (default, 'loaded');
INSERT INTO process_tracker.extract_status_lkup (extract_status_id, extract_status_name) VALUES (default, 'archived');
INSERT INTO process_tracker.extract_status_lkup (extract_status_id, extract_status_name) VALUES (default, 'deleted');
INSERT INTO process_tracker.extract_status_lkup (extract_status_id, extract_status_name) VALUES (default, 'error');

INSERT INTO process_tracker.process_status_lkup (process_status_id, process_status_name) VALUES (default, 'running');
INSERT INTO process_tracker.process_status_lkup (process_status_id, process_status_name) VALUES (default, 'completed');
INSERT INTO process_tracker.process_status_lkup (process_status_id, process_status_name) VALUES (default, 'failed');
INSERT INTO process_tracker.process_status_lkup (process_status_id, process_status_name) VALUES (default, 'on hold');


INSERT INTO process_tracker.error_type_lkup (error_type_id, error_type_name) VALUES (default, 'File Error');
INSERT INTO process_tracker.error_type_lkup (error_type_id, error_type_name) VALUES (default, 'Data Error');
INSERT INTO process_tracker.error_type_lkup (error_type_id, error_type_name) VALUES (default, 'Process Error');

INSERT INTO process_tracker.process_type_lkup (process_type_id, process_type_name) VALUES (default, 'Extract');
INSERT INTO process_tracker.process_type_lkup (process_type_id, process_type_name) VALUES (default, 'Load');

INSERT INTO process_tracker.system_lkup (system_id, system_key, system_value) VALUES (default, 'version', '0.5.0');