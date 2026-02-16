import pandas as pd
import os
#dataset
file_path = os.path.join("data", "cybersecurity_intrusion_data.csv")
df = pd.read_csv(file_path)
