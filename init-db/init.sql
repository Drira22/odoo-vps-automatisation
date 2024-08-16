CREATE DATABASE test;
\c test
\i /docker-entrypoint-initdb.d/dump.sql
