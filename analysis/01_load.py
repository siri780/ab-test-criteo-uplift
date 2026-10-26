"""Load the Criteo experiment into DuckDB and compare the two groups."""
import duckdb

con = duckdb.connect("data/criteo.duckdb")
con.execute("""
    CREATE OR REPLACE TABLE criteo AS
    SELECT * FROM read_csv_auto('data/criteo-uplift-v2.1.csv.gz')
""")

print(con.sql("SELECT COUNT(*) AS users FROM criteo"))

print(con.sql("""
    SELECT treatment,
           COUNT(*)                                            AS users,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)   AS pct_of_users,
           ROUND(100.0 * AVG(exposure), 3)                      AS exposure_rate_pct,
           ROUND(100.0 * AVG(visit), 3)                         AS visit_rate_pct,
           ROUND(100.0 * AVG(conversion), 4)                    AS conversion_rate_pct
    FROM criteo
    GROUP BY treatment
    ORDER BY treatment
"""))
