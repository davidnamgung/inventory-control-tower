import duckdb

# Connect to your processed database
db_path = '/Users/davidnamgung/portfolio-projects/inventory-control-tower/data/processed/supply_chain.duckdb'
conn = duckdb.connect(db_path)

# Query the total count and the health distribution
result = conn.execute("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE WHEN data_health = 'Needs Review' THEN 1 END) as flagged_records,
        COUNT(CASE WHEN data_health = 'Clean' THEN 1 END) as clean_records
    FROM master_parts_data
""").df()

print("--- Database Audit ---")
print(result)
conn.close()