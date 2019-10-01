SET search_path TO process_tracker;

create schema process_tracker;

alter schema process_tracker owner to pt_admin;

create table data_type_lkup
(
	data_type_id serial not null
		constraint data_type_lkup_pk
			primary key,
	data_type varchar(75) not null
);

alter table data_type_lkup owner to pt_admin;

create unique index data_type_lkup_data_type_uindex
	on data_type_lkup (data_type);



create table process_tracker.extract_filetype_lkup
(
	extract_filetype_id serial not null
		constraint extract_filetype_lkup_pk
			primary key,
	extract_filetype_code varchar(5) not null,
	extract_filetype varchar(75) not null,
	delimiter_char char,
	quote_char char,
	escape_char char
);

alter table process_tracker.extract_filetype_lkup owner to pt_admin;

create unique index extract_filetype_lkup_extract_filetype_uindex
	on process_tracker.extract_filetype_lkup (extract_filetype);




create unique index data_type_lkup_data_type_uindex
	on process_tracker.data_type_lkup (data_type);



create table process_tracker.contact_lkup
(
	contact_id serial not null
		constraint contact_lkup_pk
			primary key,
	contact_name varchar(250) not null,
	contact_email varchar(750)
);

alter table process_tracker.contact_lkup owner to pt_admin;

create unique index contact_lkup_contact_email_uindex
	on process_tracker.contact_lkup (contact_email);

create unique index contact_lkup_contact_name_uindex
	on process_tracker.contact_lkup (contact_name);

create table process_tracker.dataset_type_lkup
(
	dataset_type_id serial not null
		constraint dataset_type_lkup_pk
			primary key,
	dataset_type varchar(250)
);

comment on table process_tracker.dataset_type_lkup is 'High level of dataset type categories';

alter table process_tracker.dataset_type_lkup owner to pt_admin;

create unique index dataset_type_lkup_dataset_type_uindex
	on process_tracker.dataset_type_lkup (dataset_type);


create table error_type_lkup
(
	error_type_id serial not null
		constraint error_type_lkup_pk
			primary key,
	error_type_name varchar(250) not null
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
	error_occurrence_date_time timestamp not null
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
	tool_name varchar(250) not null
);

comment on table tool_lkup is 'List of tools that are used to run processes';

alter table tool_lkup owner to pt_admin;

create unique index tool_lkup_tool_udx01
	on tool_lkup (tool_name);

create table source_lkup
(
	source_id serial not null
		constraint source_lkup_pk
			primary key,
	source_name varchar(250) not null
);

comment on table source_lkup is 'Source system where data originates.';

alter table source_lkup owner to pt_admin;

create unique index source_lkup_udx01
	on source_lkup (source_name);

create table process_status_lkup
(
	process_status_id serial not null
		constraint process_status_lkup_pk
			primary key,
	process_status_name varchar(75) not null
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
	process_type_name varchar(250) not null
);

comment on table process_type_lkup is 'Valid process types for processes';

comment on column process_type_lkup.process_type_name is 'Unique process type name.';

alter table process_type_lkup owner to pt_admin;

create unique index process_type_lkup_udx01
	on process_type_lkup (process_type_name);

create table process
(
	process_id serial not null
		constraint process_pk
			primary key,
	process_name varchar(250) not null,
	total_record_count integer default 0 not null,
	process_type_id integer null
		constraint process_fk02
			references process_type_lkup,
	process_tool_id integer null
		constraint process_fk03
			references tool_lkup,
	last_failed_run_date_time timestamp default '1900-01-01 00:00:00'::timestamp without time zone not null
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
		primary key (child_process_id, parent_process_id)
);

comment on table process_dependency is 'Dependency tracking between processes.';

comment on column process_dependency.parent_process_id is 'The parent process.';

comment on column process_dependency.child_process_id is 'The child process.';

alter table process_dependency owner to pt_admin;

create table actor_lkup
(
	actor_id serial not null
		constraint actor_lkup_pk
			primary key,
	actor_name varchar(250) not null
);

comment on table actor_lkup is 'List of developers or applications that can run processes.';

alter table actor_lkup owner to pt_admin;

create unique index actor_lkup_udx01
	on actor_lkup (actor_name);

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
	is_latest_run boolean default false
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

create table extract_status_lkup
(
	extract_status_id serial not null
		constraint extract_status_lkup_pk
			primary key,
	extract_status_name varchar(75) not null
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
	location_type_name varchar(25) not null
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
	location_file_count integer null,
    location_bucket_name varchar(750) null
);

comment on table location_lkup is 'Locations where files are located.';

alter table location_lkup owner to pt_admin;

create unique index location_lkup_udx01
	on location_lkup (location_name);

create unique index location_lkup_udx02
	on location_lkup (location_path);

create table process_tracker.extract_compression_type_lkup
(
	extract_compression_type_id serial not null
		constraint extract_compression_type_lkup_pk
			primary key,
	extract_compression_type varchar(25) not null
);

alter table process_tracker.extract_compression_type_lkup owner to pt_admin;

create unique index extract_compression_type_lkup_extract_compression_type_uindex
	on process_tracker.extract_compression_type_lkup (extract_compression_type);



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
			references extract_filetype_lkup
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
		primary key (process_tracking_id, extract_tracking_id)
);

comment on table extract_process_tracking is 'Showing which processes have impacted which extracts';

alter table extract_process_tracking owner to pt_admin;

create table process_source
(
	source_id integer not null
		constraint process_source_fk01
			references source_lkup,
	process_id integer not null
		constraint process_source_fk02
			references process,
	constraint process_source_pk
		primary key (source_id, process_id)
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
		primary key (target_source_id, process_id)
);

comment on table process_target is 'List of targets for given processes';

alter table process_target owner to pt_admin;

create table system_lkup
(
	system_id serial not null
		constraint system_lkup_pk
			primary key,
	system_key varchar(250) not null,
	system_value varchar(250) not null
);

comment on table system_lkup is 'ProcessTracker system information';

alter table system_lkup owner to pt_admin;

create unique index system_lkup_system_key_uindex
	on system_lkup (system_key);

create table extract_dependency
(
	parent_extract_id integer not null
		constraint extract_dependency_fk01
			references extract_tracking,
	child_extract_id integer not null
		constraint extract_dependency_fk02
			references extract_tracking,
	constraint extract_dependency_pk
		primary key (parent_extract_id, child_extract_id)
);

comment on table extract_dependency is 'Table tracking interdependencies between extract files.';

alter table extract_dependency owner to pt_admin;

create table cluster_tracking
(
	cluster_id serial not null
		constraint cluster_tracking_pk
			primary key,
	cluster_name varchar(250) not null,
	cluster_max_memory integer null,
	cluster_max_memory_unit char(2) null,
	cluster_max_processing integer null,
	cluster_max_processing_unit varchar(3) null,
	cluster_current_memory_usage integer,
	cluster_current_process_usage integer
);

comment on table cluster_tracking is 'Capacity cluster tracking';

alter table cluster_tracking owner to pt_admin;

create unique index cluster_tracking_cluster_name_uindex
	on cluster_tracking (cluster_name);

create table cluster_process
(
	cluster_id integer not null
		constraint cluster_process_fk01
			references cluster_tracking,
	process_id integer not null
		constraint cluster_process_fk02
			references process,
	constraint cluster_process_pk
		primary key (cluster_id, process_id)
);

comment on table cluster_process is 'Relationship tracking between processes and performance clusters.';

alter table cluster_process owner to pt_admin;

create table process_tracker.source_object_lkup
(
	source_object_id serial not null
		constraint source_object_lkup_pk
			primary key,
	source_id integer not null
		constraint source_object_lkup_fk01
			references process_tracker.source_lkup,
	source_object_name varchar(250)
);

comment on table process_tracker.source_object_lkup is 'Reference table for source/target objects.';

alter table process_tracker.source_object_lkup owner to pt_admin;

create unique index source_object_lkup_udx01
	on process_tracker.source_object_lkup (source_id, source_object_name);

create table process_tracker.process_target_object
(
	process_id integer not null
		constraint process_target_object_fk01
			references process_tracker.process,
	target_object_id integer not null
		constraint process_target_object_fk02
			references process_tracker.source_object_lkup,
	constraint process_target_object_pk
		primary key (process_id, target_object_id)
);

comment on table process_tracker.process_target_object is 'Relationship between processes and target objects';

alter table process_tracker.process_target_object owner to pt_admin;

create table process_tracker.process_source_object
(
	process_id integer not null
		constraint process_source_object_fk01
			references process_tracker.process,
	source_object_id integer not null
		constraint process_source_object_fk02
			references process_tracker.source_object_lkup,
	constraint process_source_object_pk
		primary key (process_id, source_object_id)
);

comment on table process_tracker.process_source_object is 'Relationship between processes and source objects';

alter table process_tracker.process_source_object owner to pt_admin;

create table process_tracker.extract_dataset_type
(
	extract_id integer not null
		constraint extract_dataset_type_fk01
			references process_tracker.extract_tracking,
	dataset_type_id integer not null
		constraint extract_dataset_type_fk02
			references process_tracker.dataset_type_lkup,
	constraint extract_dataset_type_pk
		primary key (extract_id, dataset_type_id)
);

comment on table process_tracker.extract_dataset_type is 'Relationship between extract file and dataset type';

alter table process_tracker.extract_dataset_type owner to pt_admin;

create table process_tracker.process_dataset_type
(
	process_id integer not null
		constraint process_dataset_type_fk01
			references process_tracker.process,
	dataset_type_id integer not null
		constraint process_dataset_type_fk02
			references process_tracker.dataset_type_lkup,
	constraint process_dataset_type_pk
		primary key (process_id, dataset_type_id)
);

comment on table process_tracker.process_dataset_type is 'Relationship between process and dataset type';

alter table process_tracker.process_dataset_type owner to pt_admin;

create table process_tracker.source_dataset_type
(
	source_id integer not null
		constraint source_dataset_type_fk01
			references process_tracker.source_lkup,
	dataset_type_id integer not null
		constraint source_dataset_type_fk02
			references process_tracker.dataset_type_lkup,
	constraint source_dataset_type_pk
		primary key (source_id, dataset_type_id)
);

comment on table process_tracker.source_dataset_type is 'Relationship between source and dataset type';

alter table process_tracker.source_dataset_type owner to pt_admin;

create table process_tracker.source_object_dataset_type
(
	source_object_id integer not null
		constraint source_object_dataset_type_fk01
			references process_tracker.source_object_lkup,
	dataset_type_id integer not null
		constraint source_object_dataset_type_fk02
			references process_tracker.dataset_type_lkup,
	constraint source_object_dataset_type_pk
		primary key (source_object_id, dataset_type_id)
);

comment on table process_tracker.source_object_dataset_type is 'Relationship between source object and dataset type';

alter table process_tracker.source_object_dataset_type owner to pt_admin;


create table source_contact
(
	source_id integer not null
		constraint source_contact_fk01
			references source_lkup,
	contact_id integer not null
		constraint source_contact_fk02
			references contact_lkup,
	constraint source_contact_pk
		primary key (source_id, contact_id)
);

alter table source_contact owner to pt_admin;

create table process_contact
(
	process_id integer not null
		constraint process_contact_fk01
			references process,
	contact_id integer not null
		constraint process_contact_fk02
			references contact_lkup,
	constraint process_contact_pk
		primary key (process_id, contact_id)
);

alter table process_contact owner to pt_admin;

create table process_tracker.source_object_attribute
(
	source_object_attribute_id serial not null
		constraint source_object_attribute_pk
			primary key,
	source_object_attribute_name varchar(250) not null,
	source_object_id integer
		constraint source_object_attribute_fk01
			references process_tracker.source_object_lkup,
	attribute_path varchar(750),
	data_type_id integer
		constraint source_object_attribute_fk02
			references process_tracker.data_type_lkup,
	data_length integer,
	data_decimal integer,
	is_pii boolean default false not null,
	default_value_string varchar(250),
	default_value_number numeric
);

alter table process_tracker.source_object_attribute owner to pt_admin;

create unique index source_object_attribute_udx01
	on process_tracker.source_object_attribute (source_object_id, source_object_attribute_name);

create table process_tracker.process_target_object_attribute
(
	process_id integer not null
		constraint process_target_object_attribute_fk01
			references process_tracker.process,
	target_object_attribute_id integer not null
		constraint process_target_object_attribute_fk02
			references process_tracker.source_object_attribute,
	target_object_attribute_alias varchar(250),
	target_object_attribute_expression varchar(250),
	constraint process_target_object_attribute_pk
		primary key (process_id, target_object_attribute_id)
);

alter table process_tracker.process_target_object_attribute owner to pt_admin;

create table process_tracker.process_source_object_attribute
(
	process_id integer not null
		constraint process_source_object_attribute_fk01
			references process_tracker.process,
	source_object_attribute_id integer not null
		constraint process_source_object_attribute_fk02
			references process_tracker.source_object_attribute,
	source_object_attribute_alias varchar(250),
	source_object_attribute_expression varchar(250),
	constraint process_source_object_attribute_pk
		primary key (process_id, source_object_attribute_id)
);

alter table process_tracker.process_source_object_attribute owner to pt_admin;

