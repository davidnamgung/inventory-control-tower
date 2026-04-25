import duckdb
from pandas import DataFrame
import os
import shutil
import glob

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

@data_exporter
def export_data(df: DataFrame, **kwargs) -> None:
    """
    Appends new records to DuckDB and archives the raw files.
    """
    if df.empty:
        print("No data to export. Skipping.")
        return

    db_path = '/Users/davidnamgung/portfolio-projects/inventory-control-tower/data/processed/supply_chain.duckdb'
    raw_dir = '/Users/davidnamgung/portfolio-projects/inventory-control-tower/data/raw'
    archive_dir = '/Users/davidnamgung/portfolio-projects/inventory-control-tower/data/archive'
    
    # 1. Database Operations
    conn = duckdb.connect(db_path)
    tables = conn.execute("SHOW TABLES").df()
    
    # If the table already exists, APPEND. If it doesn't, CREATE.
    if 'master_parts_data' in tables['name'].values:
        conn.execute("INSERT INTO master_parts_data SELECT * FROM df")
        print(f"Successfully appended {len(df)} new records to existing DuckDB table.")
    else:
        conn.execute("CREATE TABLE master_parts_data AS SELECT * FROM df")
        print(f"Created new DuckDB table with {len(df)} initial records.")
        
    conn.close()
    
    # 2. File Archiving Operations
    all_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    for file in all_files:
        filename = os.path.basename(file)
        destination = os.path.join(archive_dir, filename)
        shutil.move(file, destination)
        print(f"Archived source file: {filename}")