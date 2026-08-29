-- Runs once on the first DB boot (as superuser). Creates the application role which:
--  - is NOT a superuser,
--  - cannot bypass RLS,
--  - is the only role the application uses (tenant isolation is forced in the DB).
create role aegispay_app login password 'aegispay';

grant connect on database aegispay to aegispay_app;
grant usage on schema public to aegispay_app;
alter default privileges in schema public
  grant select, insert, update, delete on tables to aegispay_app;
alter default privileges in schema public
  grant usage on sequences to aegispay_app;
