CREATE VIEW accounts.bcu_chequing_full AS
SELECT
  date::DATE as date,
  split_part(description, ' - ', 1) AS branch,
  CASE
    WHEN split_part(split_part(description, ' - ', 2), '  ', 1) LIKE 'Utility Bill Payment%'
      THEN 'Utility Bill Payment'
    WHEN split_part(split_part(description, ' - ', 2), '  ', 1) IN (' debit interest ','wire withdrawal')
      THEN INITCAP(trim(split_part(split_part(description, ' - ', 2), '  ', 1)))
    ELSE split_part(split_part(description, ' - ', 2), '  ', 1)
    END                             AS transaction_type,
  CASE
    WHEN description LIKE 'bloor - Utility Bill Payment  %'
      THEN substring(description FROM 31)
    WHEN description LIKE 'bloor - Utility Bill Payment %'
      THEN substring(description FROM 30)
    WHEN description LIKE 'bloor - ATM Withdrawal - %'
      THEN split_part(description, ' - ', 3)
    WHEN description LIKE 'bloor - Transfer in  %'
      THEN split_part(description, ' - ', 2)
    WHEN description LIKE 'bloor - Transfer out  %'
      THEN split_part(description, ' - ', 2)
    WHEN description LIKE 'bloor - Deposit  %'
      THEN split_part(description, ' - ', 2)
    ELSE split_part(split_part(description, ' - ', 2), '  ', 2)
    END                             AS description,
  description                       AS original_description,
  amount                            AS amount,
  balance                           AS balance
FROM accounts.bcu_chequing;

