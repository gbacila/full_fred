from full_fred.fred import Fred
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
FRED_API_KEY=os.getenv("FRED_API_KEY")

fred = Fred("/Users/gpacera/Documents/MBA/2 Year/5 Term/Python/FRED/FRED_API.txt")
fred.get_api_key_file()

fred.set_api_key_file('/Users/gpacera/Documents/MBA/2 Year/5 Term/Python/FRED/FRED_API.txt')

print(fred.env_api_key_found())
df = fred.get_series_df("GDPPOT")

print(df)