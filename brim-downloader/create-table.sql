CREATE TABLE accounts.brim_mastercard
(
  id               SERIAL PRIMARY KEY,
  number           INT,
  Transaction_Date TEXT,
  Posted_Date      TEXT,
  Description      TEXT,
  Cardmember       TEXT,
  Amount           NUMERIC,
  Points           INT,
  CATEGORY         TEXT
);
