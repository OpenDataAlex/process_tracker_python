drop database if exists process_tracking;
create database process_tracking;
create user pt_admin with password 'Testing1!';
grant all privileges on database process_tracking to pt_admin;
