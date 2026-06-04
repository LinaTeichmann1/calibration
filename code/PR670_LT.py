## PR-670 class that let's you do a basic calibration
# this is based on psychopy PR655/670 class but seems to work better for PR670
# Lina Teichmann

import time

import numpy as np
import serial


class PR670:
    """An interface to the PR670 via the serial port. -- based on Psychopy PR655 class because the combined 655/670 class did not work for me"""

    longName = "PR670"
    driverFor = ["pr670"]

    def __init__(self, port):
        self.type = None  # get this from the device later
        self.com = False
        self.OK = True  # until we fail
        if type(port) in (int, float):
            # add one so that port 1=COM1
            self.portNumber = port
            self.portString = "COM%i" % self.portNumber
        else:
            self.portString = port
            self.portNumber = None

        self.codes = {
            "OK": "000\r\n",  # this is returned after measure
            "18": "Light Low",  # returned at beginning of data
            "10": "Light Low",
            "00": "OK",
        }

        # try to open the port
        try:
            self.com = serial.Serial(self.portString)
        except Exception:
            msg = "Couldn't connect to port %s. Is it being used by another program?"
            self._error(msg % self.portString)
        # setup the params for PR670 comms
        if self.OK:
            self.com.baudrate = 115200
            # self.com.baudrate = 9600
            self.com.parity = "N"  # none
            self.com.stopbits = 1
            try:
                self.com.close()  # attempt to close if it's currently open
                self.com.open()
                self.isOpen = 1
            except Exception:
                msg = "Found a device on serial port %s, but couldn't open that port"
                self._error(msg % self.portString)
            # this should be large when making measurements
            self.com.timeout = 0.1
            self.startRemoteMode()
            self.type = self.getDeviceType()
            if self.type:
                msg = "Successfully opened %s on %s"
            else:
                self._error("PR670 isn't communicating")

    def sendMessage(self, message, timeout=100, DEBUG=False):
        """Send a command to the photometer and wait an allotted
        timeout for a response
        """
        if message[-1] != "\n":
            message += "\n"

        # flush the read buffer first
        self.com.read(self.com.inWaiting())
        time.sleep(0.5)

        # send the message
        for letter in message:
            if type(letter) != bytes:
                letter = bytes(letter, "utf-8")
            self.com.write(letter)
            self.com.flush()
            time.sleep(0.1)

        # which message was sent?
        cmd = message.strip().upper()

        # Spectrum reads (the output for spectrum-type measures are longer, this is now reading until it has a completed line with wavelength 780)
        if cmd in ("D5", "M5"):
            self.com.timeout = timeout
            lines = []
            while True:
                line = self.com.read_until(b"\n")
                if not line:
                    break
                decoded = line.decode("utf-8").strip()
                lines.append(decoded)
                try:
                    wl = int(decoded.split(",")[0])
                    if wl >= 780:
                        break
                except:
                    pass

            return lines

        # Single-line responses (this is for luminance-type measures)
        else:
            self.com.timeout = timeout
            line = self.com.read_until(b"\n")
            return line.decode("utf-8", errors="ignore").strip()

    def parseSpectrumOutput(self, rawStr):
        """Parses spectrum output from PR670 D5 command.
        Args: rawStr -- Either a single spectrum (list of "wavelength,power" strings) or RGB measurements (list of 3 such lists: [rawR, rawG, rawB])

        Returns: tuple: (wavelengths, power)
                - For single spectrum: (array of nm, array of power values)
                - For RGB: (array of nm, list of 3 arrays [R, G, B] power values)
        """
        # Check if RGB (3 measurements) or single measurement
        is_rgb = isinstance(rawStr[0], list) and len(rawStr) == 3

        if is_rgb:
            # Parse RGB measurements
            rawR, rawG, rawB = rawStr
            wavelengths = []
            power = [[], [], []]  # [R, G, B]

            for r_line, g_line, b_line in zip(rawR, rawG, rawB):
                # Parse each line: "wavelength,power\r\n"
                try:
                    nm_r, pow_r = r_line.strip().split(",")
                    nm_g, pow_g = g_line.strip().split(",")
                    nm_b, pow_b = b_line.strip().split(",")

                    # Use first wavelength (should be same for R,G,B)
                    wavelengths.append(float(nm_r))
                    power[0].append(float(pow_r))
                    power[1].append(float(pow_g))
                    power[2].append(float(pow_b))
                except (ValueError, IndexError):
                    # Skip malformed lines
                    continue

            return np.asarray(wavelengths), [np.asarray(p) for p in power]

        else:
            # Parse single spectrum measurement
            wavelengths = []
            power = []

            for line in rawStr:
                line = line.strip()

                # Skip empty lines or lines without comma
                if not line or "," not in line:
                    continue

                # Skip lines that don't have exactly 2 values (wavelength, power)
                parts = line.split(",")
                if len(parts) != 2:
                    continue

                try:
                    nm = float(parts[0])
                    pwr = float(parts[1])
                    wavelengths.append(nm)
                    power.append(pwr)
                except ValueError:
                    # Skip lines that can't be converted to float
                    continue

            return np.asarray(wavelengths), np.asarray(power)

    def measure_luminance_xy(self, timeOut=30.0):
        """This function returns [Y (luminance), x (CIE1931), y (CIE1931)]"""
        # M1: returns 5 values
        #   status
        #   units
        #   Y = photometric brightness (luminance)
        #   x = CIE1931 x
        #   y = CIE1931 y
        raw_str = self.sendMessage("M1", timeout=timeOut)
        raw = _stripLineEnds(raw_str).split(",")

        return float(raw[2]), float(raw[3]), float(raw[4])

    def measure_tristim(self, timeOut=30.0):
        """This function returns CIE1931 Tristim Values [X, Y, Z]"""
        # M2: returns 5 values
        #   status
        #   units
        #   CIE1931 Tristim Values X, Y, Z
        raw_str = self.sendMessage("M2", timeout=timeOut)
        raw = _stripLineEnds(raw_str).split(",")

        return float(raw[2]), float(raw[3]), float(raw[4])

    def measure_uv(self, timeOut=30.0):
        """This function returns [Y (luminance), u' (CIE1976), v' (CIE1976)]"""
        # M1: returns 5 values
        # M3: returns 5 values
        #   status
        #   units
        #   Y = photometric brightness (luminance)
        #   CIE 1976 u'
        #   CIE 1976 v'

        raw_str = self.sendMessage("M3", timeout=timeOut)
        raw = _stripLineEnds(raw_str).split(",")

        return float(raw[2]), float(raw[3]), float(raw[4])

    def measure_spectrum(self, timeOut=1000):
        """This function returns [nm (wavelengths) and power]"""
        # M5: returns a long list. Key ones are the ones with two items per line which have nm and power
        #   status
        #   units
        #   Peak wavelength
        #   Integrated power
        #   Integrated Photon
        #   WL
        #   Spectral data at each wavelength

        raw_str = self.sendMessage("M5", timeout=timeOut)
        # raw_str = self.sendMessage('D5')
        nm, power = self.parseSpectrumOutput(rawStr=raw_str)

        return nm, power

    # # this is to get raw (uncorrected) light and dark pixels which PR-support asks for if something is wrong wiht the device
    # def get_light_dark(self):
    #     """This function returns raw (uncorrected) light and dark pixels"""
    #     # clear buffer
    #     self.com.read(self.com.inWaiting())
    #     time.sleep(0.5)

    #     response = self.sendMessage('D8')

    #     # clean output
    #     if isinstance(response, str):
    #         lines = response.split('\n')
    #     else:
    #         lines = response
    #     light = np.array([int(line.strip().rstrip(',')) for line in lines[1:] if line.strip().rstrip(',').isdigit()])

    #     # clear buffer
    #     self.com.read(self.com.inWaiting())
    #     time.sleep(0.5)

    #     response = self.sendMessage('D9')
    #     # clean output
    #     if isinstance(response, str):
    #         lines = response.split('\n')
    #     else:
    #         lines = response
    #     dark = np.array([int(line.strip().rstrip(',')) for line in lines[1:] if line.strip().rstrip(',').isdigit()])

    #     return light, dark

    def __del__(self):
        try:
            self.endRemoteMode()
            time.sleep(0.1)
            self.com.close()
            print("Closed PR670 port")
        except Exception:
            pass

    def startRemoteMode(self):
        reply = self.sendMessage("PHOTO", timeout=10.0)

    def getDeviceType(self):
        reply = self.sendMessage("D111")  # returns errCode,
        return _stripLineEnds(reply.split(",")[-1])  # last element

    def getDeviceSN(self):
        reply = self.sendMessage("D110")  # returns errCode,
        return _stripLineEnds(reply.split(",")[-1])  # last element

    def endRemoteMode(self):
        self.com.write(b"Q")


def _stripLineEnds(s):
    return s.replace("\r", "").replace("\n", "")


if __name__ == "__main__":
    pass
