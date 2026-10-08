SELECT
    (SELECT COALESCE(SUM(inc), 0) FROM Income_o  WHERE date < '20010415')
  - (SELECT COALESCE(SUM(out), 0) FROM Outcome_o WHERE date < '20010415') AS balance
