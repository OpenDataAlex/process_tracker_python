SET search_path TO process_tracking;

create schema process_tracking;

alter schema process_tracking owner to pt_admin;

create schema process_tracking;

alter schema process_tracking owner to pt_admin;

create database process_tracking
	with owner postgres;

create sequence process_tracking.actor_lkup_actor_id_seq;

alter sequence process_tracking.actor_lkup_actor_id_seq owner to pt_admin;

create table process_tracking.error_type_lkup
(
	error_type_id serial not null
		constraint error_type_lkup_pk
			primary key,
	error_type_name varchar(250) not null
);

comment on table process_tracking.error_type_lkup is 'Types of errors that are being tracked.';

comment on column process_tracking.error_type_lkup.error_type_name is 'Unique error type name.';

alter table process_tracking.error_type_lkup owner to pt_admin;

create unique index error_type_lkup_udx01
	on process_tracking.error_type_lkup (error_type_name);

create table process_tracking.error_tracking
(
	error_tracking_id serial not null
		constraint error_tracking_pk
			primary key,
	error_type_id integer not null,
	process_tracking_id integer not null,
	error_description varchar(750),
	error_occurrence_date_time timestamp not null
);

comment on table process_tracking.error_tracking is 'Tracking of process errors';

comment on column process_tracking.error_tracking.error_type_id is 'The type of error being recorded.';

comment on column process_tracking.error_tracking.process_tracking_id is 'The specific process run that triggered the error.';

comment on column process_tracking.error_tracking.error_occurrence_date_time is 'The timestamp when the error occurred.';

alter table process_tracking.error_tracking owner to pt_admin;

create index error_tracking_idx01
	on process_tracking.error_tracking (process_tracking_id, error_type_id);

create table process_tracking.tool_lkup
(
	tool_id serial not null
		constraint tool_lkup_pk
			primary key,
	tool_name varchar(250) not null
);

comment on table process_tracking.tool_lkup is 'List of tools that are used to run processes';

alter table process_tracking.tool_lkup owner to pt_admin;

create unique index tool_lkup_tool_udx01
	on process_tracking.tool_lkup (tool_name);

create table process_tracking.source_lkup
(
	source_id serial not null
		constraint source_lkup_pk
			primary key,
	source_name varchar(250) not null
);

comment on table process_tracking.source_lkup is 'Source system where data originates.';

alter table process_tracking.source_lkup owner to pt_admin;

create unique index source_lkup_udx01
	on process_tracking.source_lkup (source_name);

create table process_tracking.process_status_lkup
(
	process_status_id serial not null
		constraint process_status_lkup_pk
			primary key,
	process_status_name varchar(75) not null
);

comment on table process_tracking.process_status_lkup is 'Process status states';

alter table process_tracking.process_status_lkup owner to pt_admin;

create unique index process_status_lkup_udx01
	on process_tracking.process_status_lkup (process_status_name);

create table process_tracking.process_type_lkup
(
	process_type_id serial not null
		constraint process_type_lkup_pk
			primary key,
	process_type_name varchar(250) not null
);

comment on table process_tracking.process_type_lkup is 'Valid process types for processes';

comment on column process_tracking.process_type_lkup.process_type_name is 'Unique process type name.';

alter table process_tracking.process_type_lkup owner to pt_admin;

create unique index process_type_lkup_udx01
	on process_tracking.process_type_lkup (process_type_name);

create table process_tracking.process
(
	process_id serial not null
		constraint process_pk
			primary key,
	process_name varchar(250) not null,
	total_record_count integer default 0 not null,
	process_type_id integer not null
		constraint process_fk02
			references process_tracking.process_type_lkup,
	process_tool_id integer not null
		constraint process_fk03
			references process_tracking.tool_lkup,
	last_failed_run_date_time timestamp default '1900-01-01 00:00:00'::timestamp without time zone not null
);

comment on table process_tracking.process is 'Processes being tracked';

comment on column process_tracking.process.process_name is 'Unique name for process.';

comment on column process_tracking.process.total_record_count is 'Total number of records processed over all runs of process.';

comment on column process_tracking.process.process_type_id is 'The type of process being tracked.';

comment on column process_tracking.process.process_tool_id is 'The type of tool used to execute the process.';

comment on column process_tracking.process.last_failed_run_date_time is 'The last time the process failed to run.';

alter table process_tracking.process owner to pt_admin;

create unique index process_udx01
	on process_tracking.process (process_name);

create table process_tracking.process_dependency
(
	parent_process_id integer not null
		constraint process_dependency_fk01
			references process_tracking.process,
	child_process_id integer not null
		constraint process_dependency_fk02
			references process_tracking.process,
	constraint process_dependency_pk
		primary key (child_process_id, parent_process_id)
);

comment on table process_tracking.process_dependency is 'Dependency tracking between processes.';

comment on column process_tracking.process_dependency.parent_process_id is 'The parent process.';

comment on column process_tracking.process_dependency.child_process_id is 'The child process.';

alter table process_tracking.process_dependency owner to pt_admin;

create table process_tracking.actor_lkup
(
	actor_id serial not null
		constraint actor_lkup_pk
			primary key,
	actor_name varchar(250) not null
);

comment on table process_tracking.actor_lkup is 'List of developers or applications that can run processes.';

alter table process_tracking.actor_lkup owner to pt_admin;

create unique index actor_lkup_udx01
	on process_tracking.actor_lkup (actor_name);

create table process_tracking.process_tracking
(
	process_tracking_id serial not null
		constraint process_tracking_pk
			primary key,
	process_id integer not null
		constraint process_tracking_fk01
			references process_tracking.process,
	process_status_id integer not null
		constraint process_tracking_fk02
			references process_tracking.process_status_lkup,
	process_run_id integer default 0 not null,
	process_run_low_date_time timestamp,
	process_run_high_date_time timestamp,
	process_run_start_date_time timestamp not null,
	process_run_end_date_time timestamp,
	process_run_record_count integer default 0,
	process_run_actor_id integer
		constraint process_tracking_fk03
			references process_tracking.actor_lkup,
	is_latest_run boolean default false
);

comment on table process_tracking.process_tracking is 'Tracking table of process runs.';

comment on column process_tracking.process_tracking.process_id is 'The process that is being run.';

comment on column process_tracking.process_tracking.process_status_id is 'The current status of the given process run.';

comment on column process_tracking.process_tracking.process_run_id is 'The unique run identifier for the process.  Sequential to the unique process.';

comment on column process_tracking.process_tracking.process_run_low_date_time is 'The lowest datetime provided by the extract dataset being processed.';

comment on column process_tracking.process_tracking.process_run_high_date_time is 'The highest datetime provided by the extract dataset being processed.';

comment on column process_tracking.process_tracking.process_run_start_date_time is 'The datetime which the process run kicked off.';

comment on column process_tracking.process_tracking.process_run_end_date_time is 'The datetime which the process run ended (either in failure or success).';

comment on column process_tracking.process_tracking.process_run_record_count is 'The number of unique records processed by the run.';

comment on column process_tracking.process_tracking.process_run_actor_id is 'The actor who kicked the process run off.';

comment on column process_tracking.process_tracking.is_latest_run is 'Flag for determining if the run record is the latest for a given process.';

alter table process_tracking.process_tracking owner to pt_admin;

create index process_tracking_idx01
	on process_tracking.process_tracking (process_id, process_status_id);

create index process_tracking_idx02
	on process_tracking.process_tracking (process_run_start_date_time, process_run_end_date_time);

create index process_tracking_idx03
	on process_tracking.process_tracking (process_run_low_date_time, process_run_high_date_time);

create table process_tracking.extract_status_lkup
(
	extract_status_id serial not null
		constraint extract_status_lkup_pk
			primary key,
	extract_status_name varchar(75) not null
);

comment on table process_tracking.extract_status_lkup is 'List of valid extract processing statuses.';

alter table process_tracking.extract_status_lkup owner to pt_admin;

create unique index extract_status_lkup_extract_status_name_uindex
	on process_tracking.extract_status_lkup (extract_status_name);

create table process_tracking.location_type_lkup
(
	location_type_id serial not null
		constraint location_type_lkup_pk
			primary key,
	location_type_name varchar(25) not null
);

comment on table process_tracking.location_type_lkup is 'Listing of location types';

alter table process_tracking.location_type_lkup owner to pt_admin;

create table process_tracking.location_lkup
(
	location_id serial not null
		constraint location_lkup_pk
			primary key,
	location_name varchar(750) not null,
	location_path varchar(750) not null,
	location_type integer not null
		constraint location_lkup_fk01
			references process_tracking.location_type_lkup
);

comment on table process_tracking.location_lkup is 'Locations where files are located.';

alter table process_tracking.location_lkup owner to pt_admin;

create unique index location_lkup_udx01
	on process_tracking.location_lkup (location_name);

create unique index location_lkup_udx02
	on process_tracking.location_lkup (location_path);

create table process_tracking.extract_tracking
(
	extract_id serial not null
		constraint extract_tracking_pk
			primary key,
	extract_filename varchar(750) not null,
	extract_location_id integer not null
		constraint extract_tracking_fk01
			references process_tracking.location_lkup,
	extract_process_run_id integer
		constraint extract_tracking_fk03
			references process_tracking.process_tracking,
	extract_status_id integer
		constraint extract_tracking_fk02
			references process_tracking.extract_status_lkup,
	extract_registration_date_time timestamp not null
);

comment on table process_tracking.extract_tracking is 'Tracking table for all extract/staging data files.';

comment on column process_tracking.extract_tracking.extract_filename is 'The unique filename for a given extract from a given source.';

comment on column process_tracking.extract_tracking.extract_location_id is 'The location where the given extract can be found.';

comment on column process_tracking.extract_tracking.extract_process_run_id is 'The process that registered or created the extract file.';

comment on column process_tracking.extract_tracking.extract_status_id is 'The status of the extract.';

comment on column process_tracking.extract_tracking.extract_registration_date_time is 'The datetime that the extract was loaded into extract tracking.';

alter table process_tracking.extract_tracking owner to pt_admin;

create table process_tracking.extract_process_tracking
(
	extract_tracking_id integer not null
		constraint extract_process_tracking_fk01
			references process_tracking.extract_tracking,
	process_tracking_id integer not null
		constraint extract_process_tracking_fk02
			references process_tracking.process_tracking,
	extract_process_event_date_time timestamp with time zone not null,
	extract_process_status_id integer
		constraint extract_process_tracking_fk03
			references process_tracking.extract_status_lkup,
	constraint extract_process_tracking_pk
		primary key (process_tracking_id, extract_tracking_id)
);

comment on table process_tracking.extract_process_tracking is 'Showing which processes have impacted which extracts';

alter table process_tracking.extract_process_tracking owner to pt_admin;

create unique index location_type_lkup_udx01
	on process_tracking.location_type_lkup (location_type_name);

create table process_tracking.process_source
(
	source_id integer not null
		constraint process_source_fk01
			references process_tracking.source_lkup,
	process_id integer not null
		constraint process_source_fk02
			references process_tracking.process,
	constraint process_source_pk
		primary key (source_id, process_id)
);

comment on table process_tracking.process_source is 'List of sources for given processes';

alter table process_tracking.process_source owner to pt_admin;

create table process_tracking.process_target
(
	target_source_id integer not null
		constraint process_target_fk01
			references process_tracking.source_lkup,
	process_id integer not null
		constraint process_target_fk02
			references process_tracking.process,
	constraint process_target_pk
		primary key (target_source_id, process_id)
);

comment on table process_tracking.process_target is 'List of targets for given processes';

alter table process_tracking.process_target owner to pt_admin;


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