
CREATE TABLE staging.questrade_rrsp
(
  action TEXT,
  commission NUMERIC,
  currency TEXT,
  description TEXT,
  grossAmount NUMERIC,
  netAmount NUMERIC,
  price NUMERIC,
  quantity NUMERIC,
  settlementDate TEXT,
  symbol TEXT,
  symbolId INT,
  tradeDate TEXT,
  transactionDate TEXT,
  type TEXT
);

CREATE TABLE staging.questrade_tfsa
(
  action TEXT,
  commission NUMERIC,
  currency TEXT,
  description TEXT,
  grossAmount NUMERIC,
  netAmount NUMERIC,
  price NUMERIC,
  quantity NUMERIC,
  settlementDate TEXT,
  symbol TEXT,
  symbolId INT,
  tradeDate TEXT,
  transactionDate TEXT,
  type TEXT
);


CREATE TABLE accounts.questrade_tfsa
(
  action TEXT,
  commission NUMERIC,
  currency TEXT,
  description TEXT,
  grossAmount NUMERIC,
  netAmount NUMERIC,
  price NUMERIC,
  quantity NUMERIC,
  settlementDate TIMESTAMPTZ,
  symbol TEXT,
  symbolId INT,
  tradeDate TIMESTAMPTZ,
  transactionDate TIMESTAMPTZ,
  type TEXT
);


CREATE TABLE accounts.questrade_rrsp
(
  action TEXT,
  commission NUMERIC,
  currency TEXT,
  description TEXT,
  grossAmount NUMERIC,
  netAmount NUMERIC,
  price NUMERIC,
  quantity NUMERIC,
  settlementDate TIMESTAMPTZ,
  symbol TEXT,
  symbolId INT,
  tradeDate TIMESTAMPTZ,
  transactionDate TIMESTAMPTZ,
  type TEXT
);


