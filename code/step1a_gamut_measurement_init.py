import json
from datetime import datetime
from pathlib import Path

from psychopy import visual

from PR670_LT import PR670

port = "COM7"
# pr = PR670(port)

####*************************#######
### HELPER FUNCTIONS #####
def take_measurement(port):
    pr = None
    print(pr)
    try:
        # luminance
        pr = PR670(port)
        print(pr)
        pr.startRemoteMode()
        lum, _, _ = pr.measure_luminance_xy()
        print(f"luminance {lum}")
        # spectrum
        nm, power = pr.measure_spectrum()
        print(f"wavelength (nm) {nm}")
        print(f"power {power}")

    except Exception as e:
        print("Communication failed:", e)

    finally:
        if pr:
            pr.endRemoteMode()
            del pr

            return lum, nm, power

def display_colour(win, stim_col=[1, 0, 0], stim_size=400):
    stim = visual.Circle(
        win, units="pix", fillColor=stim_col, colorSpace="rgb1", size=stim_size
    )
    stim.draw()
    win.flip()
    return win


def save_calibration(
    lum=[],
    nm=[],
    power=[],
    stim_rgb=[1, 0, 0],
    bg_rgb=[0.5, 0.5, 0.5],
    savepath="../outputs/",
):
    today = datetime.today().strftime("%Y%m%d")
    folder = f"{savepath}/{today}"
    Path(f"{folder}").mkdir(parents=True, exist_ok=True)

    output = {
        "date": today,
        "stim_rgb": stim_rgb,
        "bg_rgb": bg_rgb,
        "luminance": lum,
        "nm": nm,
        "power": power,
    }

    print(output)

    with open(f"{folder}/primaries.jsonl", "a") as f:
        f.write(json.dumps(output) + "\n")


####*************************#######
# take measurements of primary colours
primary_rgbs = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0], [1, 1, 1]]

win = visual.Window(
    color=[0.5, 0.5, 0.5], colorSpace="rgb1", units="pix", fullscr=True, screen=1
)
win.mouseVisible = False

for reps in range(3):
    for i, stim_col in enumerate(primary_rgbs):
        display_colour(win, stim_col, stim_size=400)
        lum, nm, power = take_measurement(port)
        save_calibration(lum, list(nm), list(power), stim_rgb=stim_col)
win.close()
