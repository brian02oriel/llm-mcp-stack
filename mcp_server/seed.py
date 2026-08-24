import sqlite3

conn = sqlite3.connect("kpi.db")
conn.executescript("""
CREATE TABLE IF NOT EXISTS revenue (
    year INTEGER, quarter INTEGER, region TEXT, amount REAL
);
DELETE FROM revenue;
INSERT INTO revenue VALUES
  (2024, 1, 'EMEA', 1250000), (2024, 2, 'EMEA', 1410000),
  (2024, 3, 'EMEA', 1180000), (2024, 4, 'EMEA', 1620000),
  (2024, 1, 'LATAM',  480000), (2024, 2, 'LATAM',  512000),
  (2024, 3, 'LATAM',  605000), (2024, 4, 'LATAM',  591000),
  (2025, 1, 'EMEA', 1390000), (2025, 1, 'LATAM',  644000);
""")
conn.commit()
conn.close()
print("seeded kpi.db")