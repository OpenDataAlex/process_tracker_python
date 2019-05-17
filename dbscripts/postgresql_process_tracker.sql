SET search_path TO process_tracking;

create schema process_tracking;

alter schema process_tracking owner to pt_admin;

create sequence actor_lkup_actor_id_seq;

alter sequence actor_lkup_actor_id_seq owner to pt_admin;

create table location_lkup
(
	location_id serial not null
		constraint location_lkup_pk
			primary key,
	location_name varchar(750) not null,
	location_path varchar(750) not null
);

comment on table location_lkup is 'Locations where files are located.';

alter table location_lkup owner to pt_admin;

create unique index location_lkup_udx01
	on location_lkup (location_name);

create unique index location_lkup_udx02
	on location_lkup (location_path);

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
	process_source_id integer not null
		constraint process_fk01
			references source_lkup,
	total_record_count integer default 0 not null,
	process_type_id integer not null
		constraint process_fk02
			references process_type_lkup,
	process_tool_id integer not null
		constraint process_fk03
			references tool_lkup,
	last_failed_run_date_time timestamp default '1900-01-01 00:00:00'::timestamp without time zone not null
);

comment on table process is 'Processes being tracked';

comment on column process.process_name is 'Unique name for process.';

comment on column process.process_source_id is 'The source that the process is extracting from.';

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
		constraint process_dependency_pk
			primary key
		constraint process_dependency_fk02
			references process
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

create table extract_tracking
(
	extract_id serial not null
		constraint extract_tracking_pk
			primary key,
	extract_source_id integer not null,
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
	extract_registration_date_time timestamp not null
);

comment on table extract_tracking is 'Tracking table for all extract/staging data files.';

comment on column extract_tracking.extract_source_id is 'Source identifier (source_lkup) for where the extract originated.';

comment on column extract_tracking.extract_filename is 'The unique filename for a given extract from a given source.';

comment on column extract_tracking.extract_location_id is 'The location where the given extract can be found.';

comment on column extract_tracking.extract_process_run_id is 'The process that registered or created the extract file.';

comment on column extract_tracking.extract_status_id is 'The status of the extract.';

comment on column extract_tracking.extract_registration_date_time is 'The datetime that the extract was loaded into extract tracking.';

alter table extract_tracking owner to pt_admin;

create unique index extract_tracking_udx01
	on extract_tracking (extract_source_id, extract_filename);

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

INSERT INTO process_tracking.extract_status_lkup (extract_status_id, extract_status_name) VALUES (1, 'initializing');
INSERT INTO process_tracking.extract_status_lkup (extract_status_id, extract_status_name) VALUES (2, 'ready');
INSERT INTO process_tracking.extract_status_lkup (extract_status_id, extract_status_name) VALUES (3, 'loading');
INSERT INTO process_tracking.extract_status_lkup (extract_status_id, extract_status_name) VALUES (4, 'loaded');
INSERT INTO process_tracking.extract_status_lkup (extract_status_id, extract_status_name) VALUES (5, 'archived');
INSERT INTO process_tracking.extract_status_lkup (extract_status_id, extract_status_name) VALUES (6, 'deleted');
INSERT INTO process_tracking.extract_status_lkup (extract_status_id, extract_status_name) VALUES (7, 'error');

INSERT INTO process_tracking.process_status_lkup (process_status_id, process_status_name) VALUES (1, 'running');
INSERT INTO process_tracking.process_status_lkup (process_status_id, process_status_name) VALUES (2, 'completed');
INSERT INTO process_tracking.process_status_lkup (process_status_id, process_status_name) VALUES (3, 'failed');