drop database if exists process_tracker;
create database process_tracker;
create user pt_admin with password 'Testing1!';
grant all privileges on database process_tracker to pt_admin;
