CREATE TABLE staging.td_visa
(
  date                    DATE,
  transaction_description TEXT,
  debit                   NUMERIC,
  credit                  NUMERIC,
  balance                 NUMERIC
);

CREATE TABLE accounts.td_visa
(
  id                      SERIAL PRIMARY KEY,
  date                    DATE,
  transaction_description TEXT,
  debit                   NUMERIC,
  credit                  NUMERIC,
  balance                 NUMERIC,
  created_at              TIMESTAMP NOT NULL DEFAULT NOW()
);
