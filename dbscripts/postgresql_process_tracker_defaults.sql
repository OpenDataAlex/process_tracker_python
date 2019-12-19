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

INSERT INTO process_tracker.system_lkup (system_id, system_key, system_value) VALUES (default, 'version', '0.9.0');

INSERT INTO process_tracker.extract_compression_type_lkup (extract_compression_type_id, extract_compression_type) VALUES (1, 'zip');

INSERT INTO process_tracker.extract_filetype_lkup (extract_filetype_id, extract_filetype_code, extract_filetype, delimiter_char, quote_char, escape_char) VALUES (1, 'csv', 'Comma Separated Values', ',', '"', '/');

INSERT INTO process_tracker.schedule_frequency_lkup (schedule_frequency_id, schedule_frequency_name) VALUES (0, 'unscheduled');
INSERT INTO process_tracker.schedule_frequency_lkup (schedule_frequency_id, schedule_frequency_name) VALUES (1, 'hourly');
INSERT INTO process_tracker.schedule_frequency_lkup (schedule_frequency_id, schedule_frequency_name) VALUES (2, 'daily');
INSERT INTO process_tracker.schedule_frequency_lkup (schedule_frequency_id, schedule_frequency_name) VALUES (3, 'weekly');
INSERT INTO process_tracker.schedule_frequency_lkup (schedule_frequency_id, schedule_frequency_name) VALUES (4, 'monthly');
INSERT INTO process_tracker.schedule_frequency_lkup (schedule_frequency_id, schedule_frequency_name) VALUES (5, 'quarterly');
INSERT INTO process_tracker.schedule_frequency_lkup (schedule_frequency_id, schedule_frequency_name) VALUES (6, 'annually');

INSERT INTO process_tracker.filter_type_lkup (filter_type_id, filter_type_code, filter_type_name) VALUES (1, 'eq', 'equal to');
INSERT INTO process_tracker.filter_type_lkup (filter_type_id, filter_type_code, filter_type_name) VALUES (2, 'lt', 'less than');
INSERT INTO process_tracker.filter_type_lkup (filter_type_id, filter_type_code, filter_type_name) VALUES (3, 'gt', 'greater than');
INSERT INTO process_tracker.filter_type_lkup (filter_type_id, filter_type_code, filter_type_name) VALUES (4, 'lte', 'less than or equal');
INSERT INTO process_tracker.filter_type_lkup (filter_type_id, filter_type_code, filter_type_name) VALUES (5, 'gte', 'greater than or equal');
INSERT INTO process_tracker.filter_type_lkup (filter_type_id, filter_type_code, filter_type_name) VALUES (6, 'not', 'not equal');
INSERT INTO process_tracker.filter_type_lkup (filter_type_id, filter_type_code, filter_type_name) VALUES (7, 'lke', 'like');
INSERT INTO process_tracker.filter_type_lkup (filter_type_id, filter_type_code, filter_type_name) VALUES (8, 'in', 'in set');

INSERT INTO process_tracker.filesize_type_lkup (filesize_type_id, filesize_type_name, filesize_type_code) VALUES (1, 'kilobytes', 'KB');
INSERT INTO process_tracker.filesize_type_lkup (filesize_type_id, filesize_type_name, filesize_type_code) VALUES (2, 'megabytes', 'MB');
INSERT INTO process_tracker.filesize_type_lkup (filesize_type_id, filesize_type_name, filesize_type_code) VALUES (3, 'gigabytes', 'GB');
INSERT INTO process_tracker.filesize_type_lkup (filesize_type_id, filesize_type_name, filesize_type_code) VALUES (4, 'bytes', 'B ');

INSERT INTO process_tracker.source_type_lkup (source_type_id, source_type_name) VALUES (1, 'Undefined');
INSERT INTO process_tracker.source_type_lkup (source_type_id, source_type_name) VALUES (2, 'Database');
INSERT INTO process_tracker.source_type_lkup (source_type_id, source_type_name) VALUES (3, 'Internal');
INSERT INTO process_tracker.source_type_lkup (source_type_id, source_type_name) VALUES (4, 'External');

INSERT INTO process_tracker.dependency_type_lkup (dependency_type_id, dependency_type_name) VALUES (1, 'Undefined');
INSERT INTO process_tracker.dependency_type_lkup (dependency_type_id, dependency_type_name) VALUES (2, 'Hard');
INSERT INTO process_tracker.dependency_type_lkup (dependency_type_id, dependency_type_name) VALUES (3, 'Soft');