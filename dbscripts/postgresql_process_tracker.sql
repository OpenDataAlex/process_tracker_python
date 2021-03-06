SET search_path TO process_tracker;

create schema process_tracker;

alter schema process_tracker owner to pt_admin;
create schema process_tracker;

alter schema process_tracker owner to pt_admin;

create table process_tracker.dependency_type_lkup
(
	dependency_type_id serial not null
		constraint dependency_type_lkup_pk
			primary key,
	dependency_type_name varchar(75) not null,
	created_date_time timestamptz default CURRENT_TIMESTAMP not null,
	created_by int default 0 not null,
	update_date_time timestamptz default CURRENT_TIMESTAMP not null,
	updated_by int default 0 not null
);

create unique index dependency_type_lkup_dependency_type_name_uindex
	on process_tracker.dependency_type_lkup (dependency_type_name);

create table dataset_type_lkup
(
	dataset_type_id serial not null
		constraint dataset_type_lkup_pk
			primary key,
	dataset_type varchar(250),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table dataset_type_lkup is 'High level of dataset type categories';

alter table dataset_type_lkup owner to pt_admin;

create unique index dataset_type_lkup_dataset_type_uindex
	on dataset_type_lkup (dataset_type);

create table error_type_lkup
(
	error_type_id serial not null
		constraint error_type_lkup_pk
			primary key,
	error_type_name varchar(250) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table error_type_lkup is 'Types of errors that are being tracked.';

comment on column error_type_lkup.error_type_name is 'Unique error type name.';

alter table error_type_lkup owner to pt_admin;

create unique index error_type_lkup_udx01
	on error_type_lkup (error_type_name);

create table error_tracking
(
	error_tracking_id serial not null
		constraint error_tracking_pk
			primary key,
	error_type_id integer not null,
	process_tracking_id integer not null,
	error_description varchar(750),
	error_occurrence_date_time timestamp not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table error_tracking is 'Tracking of process errors';

comment on column error_tracking.error_type_id is 'The type of error being recorded.';

comment on column error_tracking.process_tracking_id is 'The specific process run that triggered the error.';

comment on column error_tracking.error_occurrence_date_time is 'The timestamp when the error occurred.';

alter table error_tracking owner to pt_admin;

create index error_tracking_idx01
	on error_tracking (process_tracking_id, error_type_id);

create table tool_lkup
(
	tool_id serial not null
		constraint tool_lkup_pk
			primary key,
	tool_name varchar(250) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table tool_lkup is 'List of tools that are used to run processes';

alter table tool_lkup owner to pt_admin;

create unique index tool_lkup_tool_udx01
	on tool_lkup (tool_name);

create table process_status_lkup
(
	process_status_id serial not null
		constraint process_status_lkup_pk
			primary key,
	process_status_name varchar(75) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table process_status_lkup is 'Process status states';

alter table process_status_lkup owner to pt_admin;

create unique index process_status_lkup_udx01
	on process_status_lkup (process_status_name);

create table process_type_lkup
(
	process_type_id serial not null
		constraint process_type_lkup_pk
			primary key,
	process_type_name varchar(250) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table process_type_lkup is 'Valid process types for processes';

comment on column process_type_lkup.process_type_name is 'Unique process type name.';

alter table process_type_lkup owner to pt_admin;

create unique index process_type_lkup_udx01
	on process_type_lkup (process_type_name);

create table actor_lkup
(
	actor_id serial not null
		constraint actor_lkup_pk
			primary key,
	actor_name varchar(250) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table actor_lkup is 'List of developers or applications that can run processes.';

alter table actor_lkup owner to pt_admin;

create unique index actor_lkup_udx01
	on actor_lkup (actor_name);

create table extract_status_lkup
(
	extract_status_id serial not null
		constraint extract_status_lkup_pk
			primary key,
	extract_status_name varchar(75) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table extract_status_lkup is 'List of valid extract processing statuses.';

alter table extract_status_lkup owner to pt_admin;

create unique index extract_status_lkup_extract_status_name_uindex
	on extract_status_lkup (extract_status_name);

create table location_type_lkup
(
	location_type_id serial not null
		constraint location_type_lkup_pk
			primary key,
	location_type_name varchar(25) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table location_type_lkup is 'Listing of location types';

alter table location_type_lkup owner to pt_admin;

create unique index location_type_lkup_udx01
	on location_type_lkup (location_type_name);

create table location_lkup
(
	location_id serial not null
		constraint location_lkup_pk
			primary key,
	location_name varchar(750) not null,
	location_path varchar(750) not null,
	location_type_id integer not null
		constraint location_lkup_fk01
			references location_type_lkup,
	location_file_count integer,
	location_bucket_name varchar(750),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table location_lkup is 'Locations where files are located.';

alter table location_lkup owner to pt_admin;

create unique index location_lkup_udx01
	on location_lkup (location_name);

create unique index location_lkup_udx02
	on location_lkup (location_path);

create table system_lkup
(
	system_id serial not null
		constraint system_lkup_pk
			primary key,
	system_key varchar(250) not null,
	system_value varchar(250) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table system_lkup is 'ProcessTracker system information';

alter table system_lkup owner to pt_admin;

create unique index system_lkup_system_key_uindex
	on system_lkup (system_key);

create table cluster_tracking_lkup
(
	cluster_id serial not null
		constraint cluster_tracking_pk
			primary key,
	cluster_name varchar(250) not null,
	cluster_max_memory integer,
	cluster_max_memory_unit char(2),
	cluster_max_processing integer,
	cluster_max_processing_unit varchar(3),
	cluster_current_memory_usage integer,
	cluster_current_process_usage integer,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table cluster_tracking_lkup is 'Capacity cluster tracking';

alter table cluster_tracking_lkup owner to pt_admin;

create unique index cluster_tracking_cluster_name_uindex
	on cluster_tracking_lkup (cluster_name);

create table contact_lkup
(
	contact_id serial not null
		constraint contact_lkup_pk
			primary key,
	contact_name varchar(250) not null,
	contact_email varchar(750),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table contact_lkup owner to pt_admin;

create unique index contact_lkup_contact_email_uindex
	on contact_lkup (contact_email);

create unique index contact_lkup_contact_name_uindex
	on contact_lkup (contact_name);

create table extract_compression_type_lkup
(
	extract_compression_type_id serial not null
		constraint extract_compression_type_lkup_pk
			primary key,
	extract_compression_type varchar(25) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table extract_compression_type_lkup owner to pt_admin;

create unique index extract_compression_type_lkup_extract_compression_type_uindex
	on extract_compression_type_lkup (extract_compression_type);

create table extract_filetype_lkup
(
	extract_filetype_id serial not null
		constraint extract_filetype_lkup_pk
			primary key,
	extract_filetype_code varchar(25) not null,
	extract_filetype varchar(75) not null,
	delimiter_char char,
	quote_char char,
	escape_char char,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table extract_filetype_lkup owner to pt_admin;

create unique index extract_filetype_lkup_extract_filetype_uindex
	on extract_filetype_lkup (extract_filetype);

create table data_type_lkup
(
	data_type_id serial not null
		constraint data_type_lkup_pk
			primary key,
	data_type varchar(75) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table data_type_lkup owner to pt_admin;

create unique index data_type_lkup_data_type_uindex
	on data_type_lkup (data_type);

create table schedule_frequency_lkup
(
	schedule_frequency_id serial not null
		constraint schedule_frequency_lkup_pk
			primary key,
	schedule_frequency_name varchar(25) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table schedule_frequency_lkup owner to pt_admin;

create table process
(
	process_id serial not null
		constraint process_pk
			primary key,
	process_name varchar(250) not null,
	total_record_count integer default 0 not null,
	process_type_id integer
		constraint process_fk02
			references process_type_lkup,
	process_tool_id integer
		constraint process_fk03
			references tool_lkup,
	last_failed_run_date_time timestamp default '1900-01-01 00:00:00'::timestamp without time zone not null,
	schedule_frequency_id integer default 0 not null
		constraint process_fk04
			references schedule_frequency_lkup,
	last_completed_run_date_time timestamp default '1900-01-01 00:00:00'::timestamp without time zone not null,
	last_errored_run_date_time timestamp default '1900-01-01 00:00:00'::timestamp without time zone not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table process is 'Processes being tracked';

comment on column process.process_name is 'Unique name for process.';

comment on column process.total_record_count is 'Total number of records processed over all runs of process.';

comment on column process.process_type_id is 'The type of process being tracked.';

comment on column process.process_tool_id is 'The type of tool used to execute the process.';

comment on column process.last_failed_run_date_time is 'The last time the process failed to run.';

alter table process owner to pt_admin;

create unique index process_udx01
	on process (process_name);

create table process_dependency
(
	parent_process_id integer not null
		constraint process_dependency_fk01
			references process,
	child_process_id integer not null
		constraint process_dependency_fk02
			references process,
	constraint process_dependency_pk
		primary key (child_process_id, parent_process_id),
	dependency_type_id int default 1 not null
	    constraint process_dependency_fk03
		    references dependency_type_lkup,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table process_dependency is 'Dependency tracking between processes.';

comment on column process_dependency.parent_process_id is 'The parent process.';

comment on column process_dependency.child_process_id is 'The child process.';

alter table process_dependency owner to pt_admin;

create table process_tracking
(
	process_tracking_id serial not null
		constraint process_tracking_pk
			primary key,
	process_id integer not null
		constraint process_tracking_fk01
			references process,
	process_status_id integer not null
		constraint process_tracking_fk02
			references process_status_lkup,
	process_run_id integer default 0 not null,
	process_run_low_date_time timestamp,
	process_run_high_date_time timestamp,
	process_run_start_date_time timestamp not null,
	process_run_end_date_time timestamp,
	process_run_record_count integer default 0,
	process_run_actor_id integer
		constraint process_tracking_fk03
			references actor_lkup,
	is_latest_run boolean default false,
	process_run_name varchar(250) null,
	process_run_insert_count int default 0 not null,
	process_run_update_count int default 0 not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table process_tracking is 'Tracking table of process runs.';

comment on column process_tracking.process_id is 'The process that is being run.';

comment on column process_tracking.process_status_id is 'The current status of the given process run.';

comment on column process_tracking.process_run_id is 'The unique run identifier for the process.  Sequential to the unique process.';

comment on column process_tracking.process_run_low_date_time is 'The lowest datetime provided by the extract dataset being processed.';

comment on column process_tracking.process_run_high_date_time is 'The highest datetime provided by the extract dataset being processed.';

comment on column process_tracking.process_run_start_date_time is 'The datetime which the process run kicked off.';

comment on column process_tracking.process_run_end_date_time is 'The datetime which the process run ended (either in failure or success).';

comment on column process_tracking.process_run_record_count is 'The number of unique records processed by the run.';

comment on column process_tracking.process_run_actor_id is 'The actor who kicked the process run off.';

comment on column process_tracking.is_latest_run is 'Flag for determining if the run record is the latest for a given process.';

alter table process_tracking owner to pt_admin;

create index process_tracking_idx01
	on process_tracking (process_id, process_status_id);

create index process_tracking_idx02
	on process_tracking (process_run_start_date_time, process_run_end_date_time);

create index process_tracking_idx03
	on process_tracking (process_run_low_date_time, process_run_high_date_time);

create unique index process_tracking_udx01
	on process_tracking (process_run_name);

create table cluster_process
(
	cluster_id integer not null
		constraint cluster_process_fk01
			references cluster_tracking_lkup,
	process_id integer not null
		constraint cluster_process_fk02
			references process,
	constraint cluster_process_pk
		primary key (cluster_id, process_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table cluster_process is 'Relationship tracking between processes and performance clusters.';

alter table cluster_process owner to pt_admin;

create table process_dataset_type
(
	process_id integer not null
		constraint process_dataset_type_fk01
			references process,
	dataset_type_id integer not null
		constraint process_dataset_type_fk02
			references dataset_type_lkup,
	constraint process_dataset_type_pk
		primary key (process_id, dataset_type_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table process_dataset_type is 'Relationship between process and dataset type';

alter table process_dataset_type owner to pt_admin;

create table process_contact
(
	process_id integer not null
		constraint process_contact_fk01
			references process,
	contact_id integer not null
		constraint process_contact_fk02
			references contact_lkup,
	constraint process_contact_pk
		primary key (process_id, contact_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table process_contact owner to pt_admin;

create unique index schedule_frequency_lkup_schedule_frequency_name_uindex
	on schedule_frequency_lkup (schedule_frequency_name);

create table filter_type_lkup
(
	filter_type_id serial not null
		constraint filter_type_lkup_pk
			primary key,
	filter_type_code varchar(3) not null,
	filter_type_name varchar(75) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table filter_type_lkup owner to pt_admin;

create unique index filter_type_lkup_filter_type_code_uindex
	on filter_type_lkup (filter_type_code);

create unique index filter_type_lkup_filter_type_name_uindex
	on filter_type_lkup (filter_type_name);

create table source_type_lkup
(
	source_type_id serial not null
		constraint source_type_lkup_pk
			primary key,
	source_type_name varchar(75) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table source_type_lkup owner to pt_admin;

create unique index source_type_lkup_source_type_name_uindex
	on source_type_lkup (source_type_name);

create table character_set_lkup
(
	character_set_id serial not null
		constraint character_set_lkup_pk
			primary key,
	character_set_name varchar(75) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table character_set_lkup owner to pt_admin;

create table source_lkup
(
	source_id serial not null
		constraint source_lkup_pk
			primary key,
	source_name varchar(250) not null,
	source_type_id integer not null default 1
		constraint source_lkup_fk01
			references source_type_lkup,
	character_set_id integer
		constraint source_lkup_fk02
			references character_set_lkup,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table source_lkup is 'Source system where data originates.';

alter table source_lkup owner to pt_admin;

create unique index source_lkup_udx01
	on source_lkup (source_name);

create table process_source
(
	source_id integer not null
		constraint process_source_fk01
			references source_lkup,
	process_id integer not null
		constraint process_source_fk02
			references process,
	constraint process_source_pk
		primary key (source_id, process_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table process_source is 'List of sources for given processes';

alter table process_source owner to pt_admin;

create table process_target
(
	target_source_id integer not null
		constraint process_target_fk01
			references source_lkup,
	process_id integer not null
		constraint process_target_fk02
			references process,
	constraint process_target_pk
		primary key (target_source_id, process_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table process_target is 'List of targets for given processes';

alter table process_target owner to pt_admin;

create table source_object_lkup
(
	source_object_id serial not null
		constraint source_object_lkup_pk
			primary key,
	source_id integer not null
		constraint source_object_lkup_fk01
			references source_lkup,
	source_object_name varchar(250),
	character_set_id integer
		constraint source_object_lkup_fk02
			references character_set_lkup,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table source_object_lkup is 'Reference table for source/target objects.';

alter table source_object_lkup owner to pt_admin;

create unique index source_object_lkup_udx01
	on source_object_lkup (source_id, source_object_name);

create table process_target_object
(
	process_id integer not null
		constraint process_target_object_fk01
			references process,
	target_object_id integer not null
		constraint process_target_object_fk02
			references source_object_lkup,
	constraint process_target_object_pk
		primary key (process_id, target_object_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table process_target_object is 'Relationship between processes and target objects';

alter table process_target_object owner to pt_admin;

create table process_source_object
(
	process_id integer not null
		constraint process_source_object_fk01
			references process,
	source_object_id integer not null
		constraint process_source_object_fk02
			references source_object_lkup,
	constraint process_source_object_pk
		primary key (process_id, source_object_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table process_source_object is 'Relationship between processes and source objects';

alter table process_source_object owner to pt_admin;

create table source_dataset_type
(
	source_id integer not null
		constraint source_dataset_type_fk01
			references source_lkup,
	dataset_type_id integer not null
		constraint source_dataset_type_fk02
			references dataset_type_lkup,
	constraint source_dataset_type_pk
		primary key (source_id, dataset_type_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table source_dataset_type is 'Relationship between source and dataset type';

alter table source_dataset_type owner to pt_admin;

create table source_object_dataset_type
(
	source_object_id integer not null
		constraint source_object_dataset_type_fk01
			references source_object_lkup,
	dataset_type_id integer not null
		constraint source_object_dataset_type_fk02
			references dataset_type_lkup,
	constraint source_object_dataset_type_pk
		primary key (source_object_id, dataset_type_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table source_object_dataset_type is 'Relationship between source object and dataset type';

alter table source_object_dataset_type owner to pt_admin;

create table source_contact
(
	source_id integer not null
		constraint source_contact_fk01
			references source_lkup,
	contact_id integer not null
		constraint source_contact_fk02
			references contact_lkup,
	constraint source_contact_pk
		primary key (source_id, contact_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table source_contact owner to pt_admin;

create table source_object_attribute_lkup
(
	source_object_attribute_id serial not null
		constraint source_object_attribute_pk
			primary key,
	source_object_attribute_name varchar(250) not null,
	source_object_id integer
		constraint source_object_attribute_fk01
			references source_object_lkup,
	attribute_path varchar(750),
	data_type_id integer
		constraint source_object_attribute_fk02
			references data_type_lkup,
	data_length integer,
	data_decimal integer,
	is_pii boolean default false not null,
	default_value_string varchar(250),
	default_value_number numeric,
	is_key boolean default false not null,
	is_filter boolean default false not null,
	is_partition boolean default false not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table source_object_attribute_lkup owner to pt_admin;

create unique index source_object_attribute_udx01
	on source_object_attribute_lkup (source_object_id, source_object_attribute_name);

create table process_source_object_attribute
(
	process_id integer not null
		constraint process_source_object_attribute_fk01
			references process,
	source_object_attribute_id integer not null
		constraint process_source_object_attribute_fk02
			references source_object_attribute_lkup,
	source_object_attribute_alias varchar(250),
	source_object_attribute_expression varchar(250),
	constraint process_source_object_attribute_pk
		primary key (process_id, source_object_attribute_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table process_source_object_attribute owner to pt_admin;

create table process_target_object_attribute
(
	process_id integer not null
		constraint process_target_object_attribute_fk01
			references process,
	target_object_attribute_id integer not null
		constraint process_target_object_attribute_fk02
			references source_object_attribute_lkup,
	target_object_attribute_alias varchar(250),
	target_object_attribute_expression varchar(250),
	constraint process_target_object_attribute_pk
		primary key (process_id, target_object_attribute_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table process_target_object_attribute owner to pt_admin;

create table process_filter
(
	process_filter_id serial not null
		constraint process_filter_pk
			primary key,
	process_id integer not null
		constraint process_filter_fk01
			references process,
	source_object_attribute_id integer not null
		constraint process_filter_fk02
			references source_object_attribute_lkup,
	filter_type_id integer not null
		constraint process_filter_fk03
			references filter_type_lkup,
	filter_value_string varchar(250),
	filter_value_numeric numeric,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table process_filter owner to pt_admin;

create unique index process_filter_udx01
	on process_filter (process_id, source_object_attribute_id, filter_type_id);

create table source_location
(
	source_id integer not null
		constraint source_location_fk01
			references source_lkup,
	location_id integer not null
		constraint source_location_fk02
			references location_lkup,
	constraint source_location_pk
		primary key (source_id, location_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table source_location owner to pt_admin;

create table source_object_location
(
	source_object_id integer not null
		constraint source_object_location_fk01
			references source_object_lkup,
	location_id integer not null
		constraint source_object_location_fk02
			references location_lkup,
	constraint source_object_location_pk
		primary key (source_object_id, location_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table source_object_location owner to pt_admin;

create unique index character_set_lkup_character_set_name_uindex
	on character_set_lkup (character_set_name);

create table filesize_type_lkup
(
	filesize_type_id serial not null
		constraint filesize_type_lkup_pk
			primary key,
	filesize_type_name varchar(75) not null,
	filesize_type_code char(2) not null,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table filesize_type_lkup owner to pt_admin;

create table extract_tracking
(
	extract_id serial not null
		constraint extract_tracking_pk
			primary key,
	extract_filename varchar(750) not null,
	extract_location_id integer not null
		constraint extract_tracking_fk01
			references location_lkup,
	extract_process_run_id integer
		constraint extract_tracking_fk03
			references process_tracking,
	extract_status_id integer
		constraint extract_tracking_fk02
			references extract_status_lkup,
	extract_registration_date_time timestamp not null,
	extract_write_low_date_time timestamp,
	extract_write_high_date_time timestamp,
	extract_write_record_count integer,
	extract_load_low_date_time timestamp,
	extract_load_high_date_time timestamp,
	extract_load_record_count integer,
	extract_compression_type_id integer
		constraint extract_tracking_fk04
			references extract_compression_type_lkup,
	extract_filetype_id integer
		constraint extract_tracking_fk05
			references extract_filetype_lkup,
	extract_filesize numeric,
	extract_filesize_type_id integer
		constraint extract_tracking_fk06
			references filesize_type_lkup,
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table extract_tracking is 'Tracking table for all extract/staging data files.';

comment on column extract_tracking.extract_filename is 'The unique filename for a given extract from a given source.';

comment on column extract_tracking.extract_location_id is 'The location where the given extract can be found.';

comment on column extract_tracking.extract_process_run_id is 'The process that registered or created the extract file.';

comment on column extract_tracking.extract_status_id is 'The status of the extract.';

comment on column extract_tracking.extract_registration_date_time is 'The datetime that the extract was loaded into extract tracking.';

comment on column extract_tracking.extract_write_low_date_time is 'The lowest datetime of the data set as noted when writing the data file.';

comment on column extract_tracking.extract_write_high_date_time is 'The highest datetime of the data set as noted when writing the data file.';

comment on column extract_tracking.extract_write_record_count is 'The record count of the data set as noted when writing the data file.';

comment on column extract_tracking.extract_load_low_date_time is 'The lowest datetime of the data set as noted when loading the data file.  Should match the extract_write_low_date_time.';

comment on column extract_tracking.extract_load_high_date_time is 'The highest datetime of the data set as noted when loading the data file.';

comment on column extract_tracking.extract_load_record_count is 'The record count of the data set when loading the data file.';

alter table extract_tracking owner to pt_admin;

create table extract_process_tracking
(
	extract_tracking_id integer not null
		constraint extract_process_tracking_fk01
			references extract_tracking,
	process_tracking_id integer not null
		constraint extract_process_tracking_fk02
			references process_tracking,
	extract_process_event_date_time timestamp with time zone not null,
	extract_process_status_id integer
		constraint extract_process_tracking_fk03
			references extract_status_lkup,
	constraint extract_process_tracking_pk
		primary key (process_tracking_id, extract_tracking_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table extract_process_tracking is 'Showing which processes have impacted which extracts';

alter table extract_process_tracking owner to pt_admin;

create table extract_dependency
(
	parent_extract_id integer not null
		constraint extract_dependency_fk01
			references extract_tracking,
	child_extract_id integer not null
		constraint extract_dependency_fk02
			references extract_tracking,
	dependency_type_id int default 1 not null
	    constraint extract_dependency_fk03
		    references dependency_type_lkup,
	constraint extract_dependency_pk
		primary key (parent_extract_id, child_extract_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table extract_dependency is 'Table tracking interdependencies between extract files.';

alter table extract_dependency owner to pt_admin;

create table extract_dataset_type
(
	extract_id integer not null
		constraint extract_dataset_type_fk01
			references extract_tracking,
	dataset_type_id integer not null
		constraint extract_dataset_type_fk02
			references dataset_type_lkup,
	constraint extract_dataset_type_pk
		primary key (extract_id, dataset_type_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

comment on table extract_dataset_type is 'Relationship between extract file and dataset type';

alter table extract_dataset_type owner to pt_admin;

create table extract_source
(
	extract_id integer not null
		constraint extract_source_fk02
			references extract_tracking,
	source_id integer not null
		constraint extract_source_fk01
			references source_lkup,
	constraint extract_source_pk
		primary key (extract_id, source_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table extract_source owner to pt_admin;

create table extract_source_object
(
	extract_id integer not null
		constraint extract_source_object_fk01
			references extract_tracking,
	source_object_id integer not null
		constraint extract_source_object_fk02
			references source_object_lkup,
	constraint extract_source_object_pk
		primary key (extract_id, source_object_id),
	created_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	created_by integer default 0 not null,
	update_date_time timestamp with time zone default CURRENT_TIMESTAMP not null,
	updated_by integer default 0 not null
);

alter table extract_source_object owner to pt_admin;

create unique index filesize_type_lkup_filesize_type_code_uindex
	on filesize_type_lkup (filesize_type_code);

create unique index filesize_type_lkup_filesize_type_name_uindex
	on filesize_type_lkup (filesize_type_name);

create unique index filesize_type_lkup_udx03
	on filesize_type_lkup (filesize_type_code, filesize_type_name);


CREATE OR REPLACE FUNCTION update_date_time_trigger()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW."update_date_time" = NOW();
        RETURN NEW;
    END;
$$ language 'plpgsql';

CREATE TRIGGER actor_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.actor_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER character_set_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.character_set_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER cluster_process_update_date_time_trg BEFORE UPDATE
    ON process_tracker.cluster_process FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER cluster_tracking_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.cluster_tracking_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER contact_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.contact_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER data_type_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.data_type_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER dataset_type_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.dataset_type_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER dependency_type_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.dependency_type_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER error_tracking_update_date_time_trg BEFORE UPDATE
    ON process_tracker.error_tracking FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER error_type_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.error_type_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER extract_compression_type_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.extract_compression_type_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER extract_dataset_type_update_date_time_trg BEFORE UPDATE
    ON process_tracker.extract_dataset_type FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER extract_dependency_update_date_time_trg BEFORE UPDATE
    ON process_tracker.extract_dependency FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER extract_filetype_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.extract_filetype_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER extract_process_tracking_update_date_time_trg BEFORE UPDATE
    ON process_tracker.extract_process_tracking FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER extract_source_update_date_time_trg BEFORE UPDATE
    ON process_tracker.extract_source FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER extract_source_object_update_date_time_trg BEFORE UPDATE
    ON process_tracker.extract_source_object FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER extract_status_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.extract_status_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER extract_tracking_update_date_time_trg BEFORE UPDATE
    ON process_tracker.extract_tracking FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER filesize_type_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.filesize_type_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER filter_type_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.filter_type_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER location_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.location_type_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_contact_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_contact FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_dataset_type_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_dataset_type FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_dependency_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_dependency FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_filter_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_filter FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_source_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_source FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_source_object_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_source_object FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_source_object_attribute_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_source_object_attribute FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_status_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_status_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_target_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_target FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_target_object_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_target_object FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_target_object_attribute_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_target_object_attribute FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_tracking_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_tracking FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER process_type_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.process_type_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER schedule_frequency_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.schedule_frequency_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER source_contact_update_date_time_trg BEFORE UPDATE
    ON process_tracker.source_contact FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER source_dataset_type_update_date_time_trg BEFORE UPDATE
    ON process_tracker.source_dataset_type FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER source_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.source_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER source_location_update_date_time_trg BEFORE UPDATE
    ON process_tracker.source_location FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER source_object_attribute_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.source_object_attribute_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER source_object_dataset_type_update_date_time_trg BEFORE UPDATE
    ON process_tracker.source_object_dataset_type FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER source_object_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.source_object_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER source_object_location_update_date_time_trg BEFORE UPDATE
    ON process_tracker.source_object_location FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER source_type_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.source_type_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER system_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.system_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
CREATE TRIGGER tool_lkup_update_date_time_trg BEFORE UPDATE
    ON process_tracker.tool_lkup FOR EACH ROW EXECUTE PROCEDURE update_date_time_trigger();
