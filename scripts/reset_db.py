import duckdb
db_path = '/Users/davidnamgung/portfolio-projects/inventory-control-tower/data/processed/supply_chain.duckdb'
conn = duckdb.connect(db_path)
conn.execute("DROP TABLE IF EXISTS master_parts_data")
conn.close()
print("Database wiped. Ready for a clean run.")