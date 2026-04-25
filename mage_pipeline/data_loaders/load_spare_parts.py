import pandas as pd
import glob
import os

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@data_loader
def load_data_from_file(*args, **kwargs):
    """
    Sweeps the raw directory for any new CSV batches and combines them.
    """
    raw_dir = '/Users/davidnamgung/portfolio-projects/inventory-control-tower/data/raw'
    
    # Find all files ending in .csv
    all_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    
    if not all_files:
        print("No new files found in the raw directory.")
        return pd.DataFrame() # Return an empty dataframe to stop the pipeline gracefully
        
    print(f"Found {len(all_files)} files to process.")
    
    # Read each file and combine them into one master dataframe
    df_list = [pd.read_csv(file) for file in all_files]
    combined_df = pd.concat(df_list, ignore_index=True)
    
    return combined_df

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'