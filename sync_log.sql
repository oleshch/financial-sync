create table staging.sync_log
(
	id serial not null
		constraint sync_log_pk
			primary key,
	last_sync_date date,
	account text,
	created_at timestamp default CURRENT_TIMESTAMP
);
