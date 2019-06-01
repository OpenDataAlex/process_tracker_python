drop database if exists process_tracker;
create database process_tracker;
create user pt_admin@'%' identified by 'Testing1!';
grant all privileges on process_tracker.* to pt_admin;
