### Campus Biotech 2025 -- with PR670
We now have a new class written independent of psychopy that has the PR670 support (it's in this folder called PR670_LT.py). You need this to test the photometer. 
You may need to use two separate python environments as psyhopy is used to show the stimuli on the screen for measurement (and this requires python 3.8 or 3.10), while the colour-science package is needed to do the XYZ conversion and plotting of the chromaticies (and this requires python > 3.11). 


INSTRUCTIONS
When you plugin the PR670, check which port is connected (MAC terminal: ls /dev/tty.*)
STEP0: see whether the PR actually communicates with the computer. This takes a luminance and a spectrum measure. 
STEP1a: Do the initial gamut measurement that just tests standard R, G, B, W, K and save it (date-tagged). [This needs psychopy to show the stimuli]
STEP1b: If you took more than one primary measure, this one averages them, generates a XYZ output for black and white and a matrix for conversion, makes a chromaticity plot showing the gamut of the display. 
STEP2a: Take measurements of pre-defined RGB values. Currently it's 16 steps for RGBCMYK. 
STEP2b: Plot spectra and luminance response of the measured RGBs

After Step1a and Step2a you can use the helper script spectrum_json2csv.py to make more readable csv outputs of the json files for sharing and plotting (e.g., in Step2b)


NOTE/DEBUG
the order to turn on the PR matters:
-- plug the power cord
-- turn on by holding I button
-- wait for the shutter test (you'll hear some clicking) then connect USB
-- CHECK which port is actually connected (it changes when you have an extension cord in). On Windows: the COM may say PRI