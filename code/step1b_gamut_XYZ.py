import numpy as np 
import json
from collections import defaultdict
from datetime import datetime
from colour import sd_to_XYZ, SpectralShape, XYZ_to_xy, plotting
import matplotlib.pyplot as plt
from pathlib import Path


def avg_primary_measures(savepath = '../outputs',measurement_date=None):
    if measurement_date==None:
        today = datetime.today().strftime('%Y%m%d')
    else:
        today = measurement_date
    folder = f"{savepath}/{today}"

    # load
    data = []
    with open(f"{folder}/primaries.jsonl", "r") as f:
        for line in f:
            data.append(json.loads(line))

    # group by (date, stim_rgb, bg_rgb)
    groups = defaultdict(list)
    for entry in data:
        key = (entry["date"], tuple(entry["stim_rgb"]), tuple(entry["bg_rgb"]))
        groups[key].append(entry)

    # average
    averaged_data = []
    for key, entries in groups.items():
        avg_entry = {
            "date": key[0],
            "stim_rgb": list(key[1]),
            "bg_rgb": list(key[2]),
            "luminance": np.mean([e["luminance"] for e in entries]),
            "power": np.mean([e["power"] for e in entries], axis=0),
            "nm": np.mean([e["nm"] for e in entries], axis=0) 
        }
        averaged_data.append(avg_entry)

    return averaged_data

def get_XYZ(averaged_data):
    # get white
    filtered_entries = [entry for entry in averaged_data if entry["stim_rgb"] == [1,1,1]]
    white_power = [entry["power"] for entry in filtered_entries][0]

    # get black
    filtered_entries = [entry for entry in averaged_data if entry["stim_rgb"] == [0,0,0]]
    black_power = [entry["power"] for entry in filtered_entries][0]

    # spectral shape
    white_nm_array = np.array(filtered_entries[0]["nm"])
    shape = SpectralShape(white_nm_array[0],white_nm_array[-1],np.diff(white_nm_array)[0])

    # XYZ black and white
    XYZ_k = sd_to_XYZ(sd = black_power, shape = shape, method='Integration')
    XYZ_w = sd_to_XYZ(sd = white_power, shape = shape, method='Integration')

    # normalize such that Y_white = 1 and Y_black = 0
    XYZ_w_norm = XYZ_w-XYZ_k
    factor_white = 1/XYZ_w_norm[1]
    XYZ_w_norm = XYZ_w_norm*factor_white


    # Compute primary matrix (for converting XYZ to RGB)
    RGB_to_XYZ_matrix = np.zeros((3,3))
    for i,rgb in enumerate([[1,0,0],[0,1,0],[0,0,1]]):
        filtered_entries = [entry for entry in averaged_data if entry["stim_rgb"] == rgb]
        power = [entry["power"] for entry in filtered_entries]
        RGB_to_XYZ_matrix[:,i] = (sd_to_XYZ(sd = power, shape = shape, method='Integration'))

    XYZ_k_matrix = np.tile(XYZ_k,(3,1)).T
    RGB_to_XYZ_matrix = RGB_to_XYZ_matrix - XYZ_k_matrix

    RGB_to_XYZ_matrix = RGB_to_XYZ_matrix*factor_white
    XYZ_to_RGB_matrix = np.linalg.inv(RGB_to_XYZ_matrix)

    return XYZ_to_RGB_matrix,XYZ_w,XYZ_w_norm,XYZ_k

def visualize(averaged_data,XYZ_w,measurement_date=None):
    # transform XYZ to xy 
        # for primaries
    xy_gamut = []
    for rgb in [[1,0,0],[0,1,0],[0,0,1]]:
        filtered_entries = [entry for entry in averaged_data if entry["stim_rgb"] == rgb]
        power = [entry["power"] for entry in filtered_entries][0]
        shape = SpectralShape(np.array(filtered_entries[0]["nm"])[0],np.array(filtered_entries[0]["nm"])[-1],np.diff(np.array(filtered_entries[0]["nm"]))[0])
        xy_gamut.append(XYZ_to_xy(sd_to_XYZ(sd = power, shape = shape, method='Integration'))[0])
    xy_gamut = np.array(xy_gamut)

        # for white
    xy_white = XYZ_to_xy(XYZ_w)

    # # Plot xy - gamut (just for visualization)
    CIExyFig, CIExyax = plotting.plot_chromaticity_diagram_CIE1931(show=False)
    CIExyax.plot(
        [xy_gamut[0,0], xy_gamut[1,0], xy_gamut[2,0], xy_gamut[0,0]],  # x-coords
        [xy_gamut[0,1], xy_gamut[1,1], xy_gamut[2,1], xy_gamut[0,1]],  # y-coords
        "k-", linewidth=2, label="RGB Gamut")
    CIExyax.plot(xy_white[0],xy_white[1],"k*", label="White Point")
    CIExyax.legend()
    CIExyFig.show() 
    if measurement_date == None:
        today = datetime.today().strftime('%Y%m%d')
    else:
        today = measurement_date
    CIExyFig.savefig(f'../outputs/{today}/chromaticity_plot.png',dpi=600)


def save_XYZ(XYZ_to_RGB_matrix,XYZ_w,XYZ_w_norm,XYZ_k,savepath='../outputs/',measurement_date=None):
    if measurement_date == None:
        today = datetime.today().strftime('%Y%m%d')
    else:
        today = measurement_date
    folder = f"{savepath}/{today}"
    Path(f"{folder}").mkdir(parents=True, exist_ok=True)

    output = {
        "date": today,
        "XYZ_to_RGB_matrix": XYZ_to_RGB_matrix.tolist(),
        "XYZ_w": XYZ_w.tolist(),
        "XYZ_w_norm": XYZ_w_norm.tolist(),
        "XYZ_k": XYZ_k.tolist()
    }
    
    with open(f"{folder}/XYZ.jsonl", "w") as f:
        f.write(json.dumps(output) + "\n")




###**********************************
measurement_date = None
averaged_data = avg_primary_measures(measurement_date=measurement_date)
print(averaged_data)
XYZ_to_RGB_matrix,XYZ_w,XYZ_w_norm,XYZ_k = get_XYZ(averaged_data)
save_XYZ(XYZ_to_RGB_matrix,XYZ_w,XYZ_w_norm,XYZ_k,savepath='../outputs/',measurement_date=measurement_date)

visualize(averaged_data,XYZ_w,measurement_date=measurement_date)

plt.show(block=True)
