USE process_tracker;

create table actor_lkup
(
	actor_id int auto_increment
		primary key,
	actor_name varchar(250) not null,
	constraint actor_name
		unique (actor_name)
);

create table error_type_lkup
(
	error_type_id int auto_increment
		primary key,
	error_type_name varchar(250) not null,
	constraint error_type_name
		unique (error_type_name)
);

create table extract_status_lkup
(
	extract_status_id int auto_increment
		primary key,
	extract_status_name varchar(75) not null,
	constraint extract_status_name
		unique (extract_status_name)
);

create table location_type_lkup
(
	location_type_id int auto_increment
		primary key,
	location_type_name varchar(25) not null,
	constraint location_type_name
		unique (location_type_name)
);

create table location_lkup
(
	location_id int auto_increment
		primary key,
	location_name varchar(750) not null,
	location_path varchar(750) not null,
	location_type int null,
	location_file_count int null,
	constraint location_name
		unique (location_name),
	constraint location_path
		unique (location_path),
	constraint location_lkup_ibfk_1
		foreign key (location_type) references location_type_lkup (location_type_id)
);

create table process_tracker.extract_tracking
(
	extract_id int auto_increment
		primary key,
	extract_filename varchar(750) not null,
	extract_location_id int null,
	extract_status_id int null,
	extract_registration_date_time datetime not null,
	extract_write_low_date_time datetime null comment 'The lowest datetime of the data set as noted when writing the data file.',
	extract_write_high_date_time datetime null comment 'The highest datetime of the data set as noted when writing the data file.',
	extract_write_record_count int null comment 'The record count of the data set as noted when writing the data file.',
	extract_load_low_date_time datetime null comment 'The lowest datetime of the data set as noted when loading the data file.  Should match the extract_write_low_date_time.',
	extract_load_high_date_time datetime null comment 'The highest datetime of the data set as noted when loading the data file. Should match the extract_load_high_date_time.',
	extract_load_record_count int null comment 'The record count of the data set when loading the data file.',
	constraint extract_filename
		unique (extract_filename),
	constraint extract_tracking_ibfk_1
		foreign key (extract_location_id) references process_tracker.location_lkup (location_id),
	constraint extract_tracking_ibfk_2
		foreign key (extract_status_id) references process_tracker.extract_status_lkup (extract_status_id)
);

create index extract_location_id
	on process_tracker.extract_tracking (extract_location_id);

create index extract_status_id
	on process_tracker.extract_tracking (extract_status_id);

create table process_tracker.extract_dependency
(
	parent_extract_id int not null,
	child_extract_id int not null,
	primary key (parent_extract_id, child_extract_id),
	constraint extract_dependency_fk01
		foreign key (parent_extract_id) references process_tracker.extract_tracking (extract_id),
	constraint extract_dependency_fk02
		foreign key (child_extract_id) references process_tracker.extract_tracking (extract_id)
)
comment 'Table tracking interdependencies between extract files.';

create table process_status_lkup
(
	process_status_id int auto_increment
		primary key,
	process_status_name varchar(75) not null,
	constraint process_status_name
		unique (process_status_name)
);

create table process_type_lkup
(
	process_type_id int auto_increment
		primary key,
	process_type_name varchar(250) not null
);

create table source_lkup
(
	source_id int auto_increment
		primary key,
	source_name varchar(250) not null,
	constraint source_name
		unique (source_name)
);

create table system_lkup
(
	system_id int auto_increment
		primary key,
	system_key varchar(250) not null,
	system_value varchar(250) not null,
	constraint system_key
		unique (system_key)
);

create table tool_lkup
(
	tool_id int auto_increment
		primary key,
	tool_name varchar(250) not null,
	constraint tool_name
		unique (tool_name)
);

create table process
(
	process_id int auto_increment
		primary key,
	process_name varchar(250) not null,
	total_record_count int not null,
	process_type_id int null,
	process_tool_id int null,
	last_failed_run_date_time datetime not null,
	constraint process_name
		unique (process_name),
	constraint process_ibfk_1
		foreign key (process_type_id) references process_type_lkup (process_type_id),
	constraint process_ibfk_2
		foreign key (process_tool_id) references tool_lkup (tool_id)
);

create index process_tool_id
	on process (process_tool_id);

create index process_type_id
	on process (process_type_id);

create table process_dependency
(
	parent_process_id int not null,
	child_process_id int not null,
	primary key (parent_process_id, child_process_id),
	constraint process_dependency_ibfk_1
		foreign key (parent_process_id) references process (process_id),
	constraint process_dependency_ibfk_2
		foreign key (child_process_id) references process (process_id)
);

create index child_process_id
	on process_dependency (child_process_id);

create table process_source
(
	source_id int not null,
	process_id int not null,
	primary key (source_id, process_id),
	constraint process_source_ibfk_1
		foreign key (source_id) references source_lkup (source_id),
	constraint process_source_ibfk_2
		foreign key (process_id) references process (process_id)
);

create index process_id
	on process_source (process_id);

create table process_target
(
	target_source_id int not null,
	process_id int not null,
	primary key (target_source_id, process_id),
	constraint process_target_ibfk_1
		foreign key (target_source_id) references source_lkup (source_id),
	constraint process_target_ibfk_2
		foreign key (process_id) references process (process_id)
);

create index process_id
	on process_target (process_id);

create table process_tracking
(
	process_tracking_id int auto_increment
		primary key,
	process_id int null,
	process_status_id int null,
	process_run_id int not null,
	process_run_low_date_time datetime null,
	process_run_high_date_time datetime null,
	process_run_start_date_time datetime not null,
	process_run_end_date_time datetime null,
	process_run_record_count int not null,
	process_run_actor_id int null,
	is_latest_run tinyint(1) not null,
	constraint process_tracking_ibfk_1
		foreign key (process_id) references process (process_id),
	constraint process_tracking_ibfk_2
		foreign key (process_status_id) references process_status_lkup (process_status_id),
	constraint process_tracking_ibfk_3
		foreign key (process_run_actor_id) references actor_lkup (actor_id)
);

create table error_tracking
(
	error_tracking_id int auto_increment
		primary key,
	error_type_id int null,
	error_description varchar(750) null,
	error_occurrence_date_time datetime not null,
	process_tracking_id int null,
	constraint error_tracking_ibfk_1
		foreign key (error_type_id) references error_type_lkup (error_type_id),
	constraint error_tracking_ibfk_2
		foreign key (process_tracking_id) references process_tracking (process_tracking_id)
);

create index error_type_id
	on error_tracking (error_type_id);

create index process_tracking_id
	on error_tracking (process_tracking_id);

create table extract_process_tracking
(
	extract_tracking_id int not null,
	process_tracking_id int not null,
	extract_process_status_id int null,
	extract_process_event_date_time datetime(6) not null,
	primary key (extract_tracking_id, process_tracking_id),
	constraint extract_process_tracking_ibfk_1
		foreign key (extract_tracking_id) references extract_tracking (extract_id),
	constraint extract_process_tracking_ibfk_2
		foreign key (process_tracking_id) references process_tracking (process_tracking_id),
	constraint extract_process_tracking_ibfk_3
		foreign key (extract_process_status_id) references extract_status_lkup (extract_status_id)
);

create index extract_process_status_id
	on extract_process_tracking (extract_process_status_id);

create index process_tracking_id
	on extract_process_tracking (process_tracking_id);

create index process_id
	on process_tracking (process_id);

create index process_run_actor_id
	on process_tracking (process_run_actor_id);

create index process_status_id
	on process_tracking (process_status_id);

create table process_tracker.cluster_tracking
(
	cluster_id int auto_increment
		primary key,
	cluster_name varchar(250) not null,
	cluster_max_memory int null,
	cluster_max_memory_unit char(2) null,
	cluster_max_processing int null,
	cluster_max_processing_unit varchar(3) null,
	cluster_current_memory_usage int null,
	cluster_current_process_usage int null,
	constraint cluster_tracking_cluster_name_uindex
		unique (cluster_name)
)
comment 'Capacity cluster tracking';

create table process_tracker.cluster_process
(
	cluster_id int not null,
	process_id int not null,
	primary key (cluster_id, process_id),
	constraint cluster_process_fk01
		foreign key (cluster_id) references process_tracker.cluster_tracking (cluster_id),
	constraint cluster_process_fk02
		foreign key (process_id) references process_tracker.process (process_id)
)
comment 'Relationship tracking between processes and performance clusters.';

create table process_tracker.source_object_lkup
(
	source_object_id int auto_increment,
	source_id int not null,
	source_object_name varchar(250) null,
	constraint source_object_lkup_pk
		primary key (source_object_id),
	constraint source_object_lkup_udx01
		unique (source_id, source_object_name),
	constraint source_object_lkup_source_lkup_source_id_fk
		foreign key (source_id) references process_tracker.source_lkup (source_id)
);

create table process_tracker.process_target_object
(
	process_id int not null,
	target_object_id int not null,
	constraint process_target_object_pk
		primary key (process_id, target_object_id),
	constraint process_target_object_fk01
		foreign key (process_id) references process_tracker.process (process_id),
	constraint process_target_object_fk02
		foreign key (target_object_id) references process_tracker.source_object_lkup (source_object_id)
);

create table process_tracker.process_source_object
(
	process_id int not null,
	source_object_id int not null,
	constraint process_source_object_pk
		primary key (process_id, source_object_id),
	constraint process_source_object_fk01
		foreign key (process_id) references process_tracker.process (process_id),
	constraint process_source_object_fk02
		foreign key (source_object_id) references process_tracker.source_object_lkup (source_object_id)
);

