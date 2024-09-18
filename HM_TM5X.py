"""Data Transmitting

|BEGIN|SIZE|DEVICE ADDR|CLASS ADDR|SUBCLASS ADDR|R/W FLAG|DATA0| ... |DATA(N-1)|CHECK|END|
                  (--------------------- (N+4) BYTES ---------------------)

Data Receiving

|BEGIN|SIZE|DEVICE ADDR|CLASS ADDR|SUBCLASS ADDR|RETURN FLAG|DATA0| ... |DATA(N-1)|CHECK|END|
                  (---------------------- (N+4) BYTES ----------------------)

Steps
1. Query the Device Address, Class Address, Subclass Address and R/W
Flag of the brightness setting command.
    Query the serial communication command table in Serial
    Communication Commands to obtain the Device Address (0x36), Class
    Address (0x78), Subclass Address (0x02) and R/W Flag (write: 0x00) of
    the brightness setting command.
2. Calculate the field values: SIZE, DATA and CHK.
    - SIZE: N+4. The number of bytes for the DATA field of the brightness
    setting command is N=1, so the SIZE is 5 (0x05).
    - DATA: The hexadecimal value corresponding to the brightness of 100
    is 0x64.
    - CHK: The summation 0x(36+78+02+00+64)=0x114, take the lower 8
    bits for the CHK field, that is 0x14.
3. Combining the above parameters, the host sends the command
    0x F0 05 36 78 02 00 64 14 FF
to the module.
4. The module feeds back the command
    0x F0 05 36 78 02 03 01 B4 FF
    - SIZE: N+4. The number of bytes for the DATA field of the brightness
    setting command is N=1, so the SIZE is 5 (0x05).
    - DATA: The module receives the brightness setting command and
    returns 0x01.
    - CHK: The summation 0x(36+78+02+00+01)=0xB4, take the lower 8
    bits for the CHK field, that is 0xB4.
5. Check whether the screen brightness changes to determine whether the
setting is successful, or you can use the brightness query command to
check it.

"""

BEGIN = 0xF0
DEVICE_ADDR = 0x36
WRITE_FLAG = 0x00
READ_FLAG = 0x01
NORMAL_RETURN = 0x03
ERROR_RETURN = 0x04
NO_DATA = 0x00
END = 0xFF

""" 1: readModel()
    2: readFPGAVersionNumber()
    3: writeSaveCurrentSettings()
    4: writeFactoryReset()
    5: writeManualShutterCalibration()
    6: writeBackgroundCorrection()
    7: writeVignettingCorrection()
    8: autoShutterControl()
    9: brightness()
    10: contrast()
    11: imageDetailDigitalEnhancement()
    12: staticDenoisingLevel()
    13: dynamicDenoisingLevel()
    14: palette()
    15: imageMirroring()
"""


def handleReply(t: str, function: int):
    match function:
        case 1:
            return parseReadModel(t)
        case 2:
            return parseFPGAVersionNumber(t)
        case 3:
            return parseSaveCurrentSettings(t)
        case 4:
            return parseFactoryReset(t)
        case 5:
            return parseManualShutterCalibration(t)
        case 6:
            return parseBackgroundCorrection(t)
        case 7:
            return parseVignettingCorrection(t)
        case 8:
            return parseAutoShutterControl(t)
        case 9:
            return parseBrightness(t)
        case 10:
            return parseContrast(t)
        case 11:
            return parseImageDetailDigitalEnhancement(t)
        case 12:
            return parseStaticDenoisingLevel(t)
        case 13:
            return parseDynamicDenoisingLevel(t)
        case 14:
            return parsePalette(t)
        case 15:
            return parseImageMirroring(t)


def parseFeedback(text: str, class_addr: int, subclass_addr: int):
    text_ = text
    text_len = len(text)
    text = text[2:]  # drop '0x'
    text_len -= 2
    begin = int("0x" + text[:2], 0)
    if begin != BEGIN:
        print("parse error: begin does not match")
        return f"-1 parse error: begin does not match: {text_}"
    text = text[2:]

    size = int("0x" + text[:2], 0)
    data_size = size - 4
    if data_size < 1:
        print("parse error: data_size < 1")
        return f"-1 parse error: data_size < 1: {text_}"
    if data_size + 8 != text_len / 2:
        print("parse error: size does not match packet length")
        return f"-1 parse error: size does not match packet length: {text_}"
    text = text[2:]

    device_addr = int("0x" + text[:2], 0)
    if device_addr != DEVICE_ADDR:
        print("parse error: device_addr does not match")
        return f"-1 parse error: device_addr does not match: {text_}"
    text = text[2:]

    class_addr_ = int("0x" + text[:2], 0)
    if class_addr_ != class_addr:
        print("parse error: class_addr does not match")
        return f"-1 parse error: class_addr does not match: {text_}"
    text = text[2:]

    subclass_addr_ = int("0x" + text[:2], 0)
    if subclass_addr_ != subclass_addr:
        print("parse error: class_addr does not match")
        return f"-1 parse error: class_addr does not match: {text_}"
    text = text[2:]

    flag = int("0x" + text[:2], 0)
    if flag != NORMAL_RETURN:
        print("parse error: return flag is not normal")
        return f"-1 parse error: return flag is not normal: {text_}"
    text = text[2:]

    data = int("0x" + text[: 2 * data_size], 0)
    text = text[2 * data_size :]

    chk = int("0x" + text[:2], 0)
    chk_val = (device_addr + class_addr + subclass_addr + flag + data) & 0xFF
    if chk != chk_val:
        print("parse error: check does not match")
        return f"-1 parse error: check does not match: {text_}"
    text = text[2:]

    end = int("0x" + text[:2], 0)
    if end != END:
        print("parse error: end does not match")
        return f"-1 parse error: end does not match: {text_}"

    return str(data)


def parseFeedbackWithoutClass(feedback: str):
    feedback_len = len(feedback)
    if feedback_len < 20:
        return 0
    feedback = feedback[2:]  # drop '0x'
    feedback_len -= 2
    begin = int("0x" + feedback[:2], 0)
    if begin != BEGIN:
        print("parse error: begin does not match")
        return "-1"
    feedback = feedback[2:]

    size = int("0x" + feedback[:2], 0)
    data_size = size - 4
    if data_size < 1:
        print("parse error: data_size < 1")
        return "-1"
    if data_size + 8 != feedback_len / 2:
        print("parse error: size does not match packet length")
        return "-1"
    feedback = feedback[2:]

    device_addr = int("0x" + feedback[:2], 0)
    if device_addr != DEVICE_ADDR:
        print("parse error: device_addr does not match")
        return "-1"
    feedback = feedback[2:]

    class_addr_ = int("0x" + feedback[:2], 0)
    # if class_addr_ != class_addr:
    #     print('parse error: class_addr does not match')
    #     return "-1"
    feedback = feedback[2:]

    subclass_addr_ = int("0x" + feedback[:2], 0)
    # if subclass_addr_ != subclass_addr:
    #     print('parse error: class_addr does not match')
    #     return "-1"
    feedback = feedback[2:]

    flag = int("0x" + feedback[:2], 0)
    if flag != NORMAL_RETURN:
        print("parse error: return flag is not normal")
        return "-1"
    feedback = feedback[2:]

    data = int("0x" + feedback[: 2 * data_size], 0)
    feedback = feedback[2 * data_size :]

    chk = int("0x" + feedback[:2], 0)
    chk_val = (device_addr + class_addr_ + subclass_addr_ + flag + data) & 0xFF
    if chk != chk_val:
        print("parse error: check does not match")
        return "-1"
    feedback = feedback[2:]

    end = int("0x" + feedback[:2], 0)
    if end != END:
        print("parse error: end does not match")
        return "-1"

    return data


def packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk):
    vals = [
        BEGIN,
        size,
        DEVICE_ADDR,
        class_addr,
        subclass_addr,
        rw_flag,
        data,
        chk,
        END,
    ]
    output = ""
    for val in vals:
        output += f"{val:02X}"
    return output


# 2.2.1 Reading the Model of the Module (Read-Only)
def readModel():
    class_addr = 0x74
    subclass_addr = 0x02
    rw_flag = READ_FLAG
    data = 0x00
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseReadModel(feedback):
    data = parseFeedback(feedback, class_addr=0x74, subclass_addr=0x02)
    if data[:2] == "-1":
        return data
    print(data)
    return bytes.fromhex(hex(int(data))[2:]).decode("ascii")


# 2.2.2 Reading the FPGA Program Version Number (Read-Only)
def FPGAVersionNumber():
    class_addr = 0x74
    subclass_addr = 0x03
    rw_flag = READ_FLAG
    data = 0x00
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseFPGAVersionNumber(feedback):
    data = parseFeedback(feedback, class_addr=0x74, subclass_addr=0x03)
    if data[:2] == "-1":
        return data
    data = data[2:]  # drop '0x'
    if len(data) != 6:
        return "-1 data is not 3 bytes long"
    return f"{int(data[:2])}.{int(data[2:4])}.{int(data[4:])}"


# 2.2.8 Saving Current Settings (Write-Only)
def saveCurrentSettings():
    class_addr = 0x74
    subclass_addr = 0x10
    rw_flag = WRITE_FLAG
    data = 0x00
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseSaveCurrentSettings(feedback):
    data = parseFeedback(feedback, class_addr=0x74, subclass_addr=0x10)
    if data[:2] == "-1":
        return data
    if int(data) != 0x01:
        return "-1 data != 0x01"
    return data


# 2.2.9 Factory Reset (Write-Only)
def factoryReset():
    class_addr = 0x74
    subclass_addr = 0x0F
    rw_flag = WRITE_FLAG
    data = 0x00
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseFactoryReset(feedback):
    data = parseFeedback(feedback, class_addr=0x74, subclass_addr=0x0F)
    if data[:2] == "-1":
        return data
    if int(data) != 0x01:
        return "-1 data != 0x01"
    return data


# 2.2.10 Manual Shutter Calibration (Write-Only)
def manualShutterCalibration():
    class_addr = 0x7C
    subclass_addr = 0x02
    rw_flag = WRITE_FLAG
    data = 0x00
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseManualShutterCalibration(feedback):
    data = parseFeedback(feedback, class_addr=0x7C, subclass_addr=0x02)
    if data[:2] == "-1":
        return data
    if int(data) != 0x01:
        return "-1 data != 0x01"
    return data


# 2.2.11 Manual Background Correction (Write-Only)
def manualBackgroundCorrection():
    class_addr = 0x7C
    subclass_addr = 0x03
    rw_flag = WRITE_FLAG
    data = 0x00
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseBackgroundCorrection(feedback):
    data = parseFeedback(feedback, class_addr=0x7C, subclass_addr=0x03)
    if data[:2] == "-1":
        return data
    if int(data) != 0x01:
        return "-1 data != 0x01"
    return data


# 2.2.12 Vignetting Correction (Write-Only)
def vignettingCorrection():
    class_addr = 0x7C
    subclass_addr = 0x02
    rw_flag = WRITE_FLAG
    data = 0x00
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseVignettingCorrection(feedback):
    data = parseFeedback(feedback, class_addr=0x7C, subclass_addr=0x02)
    if data[:2] == "-1":
        return data
    if int(data) != 0x01:
        return "-1 data != 0x01"
    return data


# 2.2.13 Automatic Shutter Control (Read/Write)
# data values:
#   0 = Automatic control off
#   1 = Automatic switching, timing control
#   2 = Automatic switch, temperature difference control
#   3 = Full-automatic control (default)
def autoShutterControl(data=0x00, write=False):
    if write and (data < 0 or data > 3):
        print(f"data must be between 0x00 and 0x03 when writing, given {data}")
        return f"-1 data must be between 0x00 and 0x03 when writing, given {data}"
    if not write and data != 0x00:
        print(f"data must be between 0x00 when reading, given {data}")
        return f"-1 data must be between 0x00 when reading, given {data}"
    class_addr = 0x7C
    subclass_addr = 0x04
    rw_flag = WRITE_FLAG if write else READ_FLAG
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseAutoShutterControl(feedback):
    data = parseFeedback(feedback, class_addr=0x7C, subclass_addr=0x04)
    if data[:2] == "-1":
        return data
    if int(data) < 0 or int(data) > 3:
        print(f"data must be between 0x00 and 0x03, got {data}")
        return f"-1 data must be between 0x00 and 0x03, got {data}"
    values = [
        "Automatic control off",
        "Automatic switching, timing control",
        "Automatic switch, temperature difference control",
        "Full-automatic control (default)",
    ]
    return values[int(data)]


# 2.2.16 Brightness (Read/Write)
# data values:
#   range of 0-100 (decimal), default is 50
def brightness(data=0x00, write=False):
    if write and (data < 0 or data > 100):
        print(f"data must be between 0 and 100 when writing, given {data}")
        return f"-1 data must be between 0 and 100 when writing, given {data}"
    if not write and data != 0x00:
        print(f"data must be between 0x00 when reading, given {data}")
        return f"-1 data must be between 0x00 when reading, given {data}"
    class_addr = 0x78
    subclass_addr = 0x02
    rw_flag = WRITE_FLAG if write else READ_FLAG
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseBrightness(feedback):
    data = parseFeedback(feedback, class_addr=0x78, subclass_addr=0x02)
    if data[:2] == "-1":
        return data
    if int(data) < 0 or int(data) > 100:
        print(f"data must be between 0 and 100, got {data}")
        return f"-1 data must be between 0 and 100, got {data}"
    return data


# 2.2.17 Contrast (Read/Write)
# data values:
#   range of 0-100 (decimal), default is 50
def contrast(data=0x00, write=False):
    if write and (data < 0 or data > 100):
        print(f"data must be between 0 and 100 when writing, given {data}")
        return f"-1 data must be between 0 and 100 when writing, given {data}"
    if not write and data != 0x00:
        print(f"data must be between 0x00 when reading, given {data}")
        return f"-1 data must be between 0x00 when reading, given {data}"
    class_addr = 0x78
    subclass_addr = 0x03
    rw_flag = WRITE_FLAG if write else READ_FLAG
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseContrast(feedback):
    data = parseFeedback(feedback, class_addr=0x78, subclass_addr=0x03)
    if data[:2] == "-1":
        return data
    if int(data) < 0 or int(data) > 100:
        print(f"data must be between 0 and 100, got {data}")
        return f"-1 data must be between 0 and 100, got {data}"
    return data


# 2.2.18 Image Detail Digital Enhancement (Read/Write)
# data values:
#   range of 0-100 (decimal), default is 50
def imageDetailDigitalEnhancement(data=0x00, write=False):
    if write and (data < 0 or data > 100):
        print(f"data must be between 0 and 100 when writing, given {data}")
        return f"-1 data must be between 0 and 100 when writing, given {data}"
    if not write and data != 0x00:
        print(f"data must be between 0x00 when reading, given {data}")
        return f"-1 data must be between 0x00 when reading, given {data}"
    class_addr = 0x78
    subclass_addr = 0x10
    rw_flag = WRITE_FLAG if write else READ_FLAG
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseImageDetailDigitalEnhancement(feedback):
    data = parseFeedback(feedback, class_addr=0x78, subclass_addr=0x10)
    if data[:2] == "-1":
        return data
    if int(data) < 0 or int(data) > 100:
        print(f"data must be between 0 and 100, got {data}")
        return f"-1 data must be between 0 and 100, got {data}"
    return data


# 2.2.19 Static Denoising Level (Read/Write)
# data values:
#   range of 0-100 (decimal), default is 50
def staticDenoisingLevel(data=0x00, write=False):
    if write and (data < 0 or data > 100):
        print(f"data must be between 0 and 100 when writing, given {data}")
        return f"-1 data must be between 0 and 100 when writing, given {data}"
    if not write and data != 0x00:
        print(f"data must be between 0x00 when reading, given {data}")
        return f"-1 data must be between 0x00 when reading, given {data}"
    class_addr = 0x78
    subclass_addr = 0x15
    rw_flag = WRITE_FLAG if write else READ_FLAG
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseStaticDenoisingLevel(feedback):
    data = parseFeedback(feedback, class_addr=0x78, subclass_addr=0x15)
    if data[:2] == "-1":
        return data
    if int(data) < 0 or int(data) > 100:
        print(f"data must be between 0 and 100, got {data}")
        return f"-1 data must be between 0 and 100, got {data}"
    return data


# 2.2.20 Dynamic Denoising Level (Read/Write)
# data values:
#   range of 0-100 (decimal), default is 50
def dynamicDenoisingLevel(data=0x00, write=False):
    if write and (data < 0 or data > 100):
        print(f"data must be between 0 and 100 when writing, given {data}")
        return f"-1 data must be between 0 and 100 when writing, given {data}"
    if not write and data != 0x00:
        print(f"data must be between 0x00 when reading, given {data}")
        return f"-1 data must be between 0x00 when reading, given {data}"
    class_addr = 0x78
    subclass_addr = 0x16
    rw_flag = WRITE_FLAG if write else READ_FLAG
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseDynamicDenoisingLevel(feedback):
    data = parseFeedback(feedback, class_addr=0x78, subclass_addr=0x16)
    if data[:2] == "-1":
        return data
    if int(data) < 0 or int(data) > 100:
        print(f"data must be between 0 and 100, got {data}")
        return f"-1 data must be between 0 and 100, got {data}"
    return data


# 2.2.21 palette (Read/Write)
# data values:
#   0x00: White Hot (default)
#   0x01: Black Hot
#   0x02: Fusion 1
#   0x03: Rainbow
#   0x04: Fusion 2
#   0x05: Iron Red 1
#   0x06: Iron Red 2
#   0x07: Dark Brown
#   0x08: Color 1
#   0x09: Color 2
#   0x0A: Ice Fire
#   0x0B: Rain
#   0x0C: Green Hot
#   0x0D: Red Hot
#   0x0E: Deep Blue
#
#   Palette switching will take a while. You need to wait after sending the
#   command to check the switching result
def palette(data=0x00, write=False):
    if write and (data < 0 or data > 0x0E):
        print(f"data must be between 0x00 and 0x0E when writing, given {data}")
        return f"-1 data must be between 0x00 and 0x0E when writing, given {data}"
    if not write and data != 0x00:
        print(f"data must be between 0x00 when reading, given {data}")
        return f"-1 data must be between 0x00 when reading, given {data}"
    class_addr = 0x78
    subclass_addr = 0x20
    rw_flag = WRITE_FLAG if write else READ_FLAG
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parsePalette(feedback):
    data = parseFeedback(feedback, class_addr=0x78, subclass_addr=0x20)
    if data[:2] == "-1":
        return data
    if int(data) < 0 or int(data) > 0x0E:
        print(f"data must be between 0x00 and 0x0E, got {data}")
        return f"-1 data must be between 0x00 and 0x0E, got {data}"
    values = [
        "White Hot",
        "Black Hot",
        "Fusion 1",
        "Rainbow",
        "Fusion 2",
        "Iron Red 1",
        "Iron Red 2",
        "Dark Brown",
        "Color 1",
        "Color 2",
        "Ice Fire",
        "Rain",
        "Green Hot",
        "Red Hot",
        "Deep Blue",
    ]
    return values[int(data)]


# 2.2.22 ImageMirroring (Read/Write)
# data values:
#   0x00: No mirroring
#   0x01: Central mirroring
#   0x02: Left/right mirroring
#   0x03: Up/down mirroring
def imageMirroring(data=0x00, write=False):
    if write and (data < 0 or data > 0x03):
        print(f"data must be between 0x00 and 0x03 when writing, given {data}")
        return f"-1 data must be between 0x00 and 0x03 when writing, given {data}"
    if not write and data != 0x00:
        print(f"data must be between 0x00 when reading, given {data}")
        return f"-1 data must be between 0x00 when reading, given {data}"
    class_addr = 0x70
    subclass_addr = 0x11
    rw_flag = WRITE_FLAG if write else READ_FLAG
    size = 0x05
    chk = (DEVICE_ADDR + class_addr + subclass_addr + rw_flag + data) & 0xFF
    return packetTemplate(class_addr, subclass_addr, rw_flag, data, size, chk)


def parseImageMirroring(feedback):
    data = parseFeedback(feedback, class_addr=0x70, subclass_addr=0x11)
    if data[:2] == "-1":
        return data
    if int(data) < 0 or int(data) > 0x03:
        print(f"data must be between 0x00 and 0x03, got {data}")
        return f"-1 data must be between 0x00 and 0x03, got {data}"
    values = [
        "no mirroring",
        "central mirroring",
        "left/right mirroring",
        "up/down mirroring",
    ]
    return values[int(data)]
