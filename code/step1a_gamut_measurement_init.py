import json
from datetime import datetime
from pathlib import Path
from psychopy import visual, event
import numpy as np
from PR670_LT import PR670

port = "COM3"
isviewpixx = 1
isfullscreen = 1
screen = 1

if isviewpixx==True:
    from pypixxlib import _libdpx as dp
    dp.DPxOpen()

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


def viewpixx_research_mode_on(isviewpixx=False):
        is_research=0
        while is_research == 0:
            # Enable Research Mode - CALL THIS OFTEN DURING EXPERIMENTS TO AVOID TIMEOUT
            dp.VP3EnableResearchMode()
            dp.DPxWriteRegCache()   
            # Check status - start with a register update to ensure values are current 
            dp.DPxUpdateRegCache()   
            is_research = dp.VP3IsResearchMode()
            print(dp)
            print(f"VIEWPIXX research mode {is_research}")

def viewpixx_research_mode_off(isviewpixx=False):
    if isviewpixx:
        from pypixxlib import _libdpx as dp
        # Disable Research Mode
        dp.VP3DisableResearchMode()
        dp.DPxWriteRegCache()  

        # Check status - start with a register update to ensure values are current 
        dp.DPxUpdateRegCache()   
        is_research = dp.VP3IsResearchMode()
        print(f"VIEWPIXX research mode {is_research}")

def look_for_responses(exit_keys=["q"],isviewpixx=False):
    print('looking for responses')
    pressed = event.getKeys(keyList=exit_keys, modifiers=False)
    if np.any(pressed):
        print(pressed)
        if pressed ==["q"]:
            print("user quit experiment")
            
            if isviewpixx:
                viewpixx_research_mode_off(isviewpixx)
            win.close()

####*************************#######
# take measurements of primary colours
primary_rgbs = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0], [1, 1, 1]]

win = visual.Window(color=[0.5, 0.5, 0.5], colorSpace="rgb1", units="pix", fullscr=isfullscreen, screen=screen)
win.mouseVisible = False

for reps in range(3):
    viewpixx_research_mode_on(isviewpixx)
    for i, stim_col in enumerate(primary_rgbs):
        for _ in range(100):
            display_colour(win, stim_col, stim_size=400)
            look_for_responses(isviewpixx=isviewpixx)
        lum, nm, power = take_measurement(port)
        save_calibration(lum, list(nm), list(power), stim_rgb=stim_col)

win.close()
viewpixx_research_mode_off(isviewpixx)
