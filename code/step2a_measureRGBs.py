from psychopy import visual
from PR670_LT import PR670
from datetime import datetime
from pathlib import Path
import json
import numpy as np


port = '/dev/tty.usbmodem3101'
pr = PR670(port)
n_steps = 16

####*************************#######
### HELPER FUNCTIONS #####
def take_measurement(port):
    pr = None
    try:
        # luminance
        pr = PR670(port)
        pr.startRemoteMode()
        lum,_,_ = pr.measure_luminance_xy()
        print(f'luminance {lum}')
        # spectrum
        nm,power = pr.measure_spectrum()
        print(f'wavelength (nm) {nm}')
        print(f'power {power}')

    except Exception as e:
        print("Communication failed:", e)

    finally:
        if pr:
            pr.endRemoteMode()
            del pr

            return lum,nm,power

def display_colour(win, stim_col = [1,0,0], stim_size=400):
    stim = visual.Circle(win,units='pix',fillColor=stim_col, colorSpace='rgb1',size=stim_size)
    stim.draw()
    win.flip()    
    return win

def save_calibration(lum=[],nm=[],power=[],stim_rgb=[1,0,0],bg_rgb=[0.5,0.5,0.5],savepath='../outputs/'):
    today = datetime.today().strftime('%Y%m%d')
    folder = f"{savepath}/{today}"
    Path(f"{folder}").mkdir(parents=True, exist_ok=True)

    output = {
        "date": today,
        "stim_rgb": stim_rgb,
        "bg_rgb": bg_rgb,
        "luminance": lum,
        "nm": nm,
        "power": power}
    
    print(output)

    with open(f"{folder}/measured_rgbs.jsonl", "a") as f:
        f.write(json.dumps(output) + "\n")


####*************************#######
# take measurements of predefined colours 
steps = np.linspace(0, 1, n_steps)

rgb_dict = {}
channels = [
    (1, 0, 0),  # R
    (0, 1, 0),  # G
    (0, 0, 1),  # B
    (1, 1, 0),  # Y
    (1, 0, 1),  # M
    (0, 1, 1),  # C
    (1, 1, 1),  # W
]

for r_on, g_on, b_on in channels:
    for s in steps:
        rgb = (float(s * r_on),float(s * g_on),float(s * b_on))
        rgb_dict[rgb] = None  # dict removes duplicates automatically

# Add black once
rgb_dict[(0.0, 0.0, 0.0)] = None
measured_rgbs = np.array(list(rgb_dict.keys()))
measured_rgbs = measured_rgbs.tolist()
print(measured_rgbs)
print(len(measured_rgbs))

win = visual.Window(color=[0.5,0.5,0.5],colorSpace='rgb1',units='pix',fullscr=True)
win.mouseVisible = False        

for i,stim_col in enumerate(measured_rgbs):
    display_colour(win, stim_col, stim_size=400)
    lum,nm,power = take_measurement(port)
    save_calibration(lum,list(nm),list(power),stim_rgb=stim_col)
win.close()
        
