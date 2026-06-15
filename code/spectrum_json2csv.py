import json
import pandas as pd
from datetime import datetime

# check when this was measured
measurement_date = None
if measurement_date==None:
    today = datetime.today().strftime('%Y%m%d')
else:
    today = measurement_date
jsonl_file = f"../outputs/{today}/measured_rgbs.jsonl"
output_file = f"../outputs/{today}/measured_rgbs.csv"

# Read JSONL file
records = []
with open(jsonl_file, "r") as f:
    for line in f:
        records.append(json.loads(line))

# Convert to tidy rows
rows = []
for rec in records:
    row = {
        "date": rec["date"],
        "stim_r": rec["stim_rgb"][0],
        "stim_g": rec["stim_rgb"][1],
        "stim_b": rec["stim_rgb"][2],
        "bg_r": rec["bg_rgb"][0],
        "bg_g": rec["bg_rgb"][1],
        "bg_b": rec["bg_rgb"][2],
        "luminance": rec["luminance"],
    }

    for nm, power in zip(rec["nm"], rec["power"]):
        row[f"{int(nm)}nm"] = power

    rows.append(row)

# Create dataframe & save as csv
df = pd.DataFrame(rows)
df.to_csv(output_file, index=False)
