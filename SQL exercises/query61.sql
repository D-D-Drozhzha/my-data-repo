SELECT
(SELECT COALESCE(SUM(inc), 0) FROM Income_o)
- (SELECT COALESCE(SUM(out), 0) FROM Outcome_o) AS balance;
