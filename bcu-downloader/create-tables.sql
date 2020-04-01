----- Staging Tables -----

create table staging.bcu_bculink_savings
(
	date text,
	description text,
	amount numeric,
	balance numeric
);

create table staging.bcu_chequing
(
	date text,
	description text,
	amount numeric,
	balance numeric
);

create table staging.bcu_daily_savings
(
	date text,
	description text,
	amount numeric,
	balance numeric
);

----- Account Tables -----

create table accounts.bcu_bculink_savings
(
	date text,
	description text,
	amount numeric,
	balance numeric
);

create table accounts.bcu_chequing
(
	date text,
	description text,
	amount numeric,
	balance numeric
);

create table accounts.bcu_daily_savings
(
	date text,
	description text,
	amount numeric,
	balance numeric
);
