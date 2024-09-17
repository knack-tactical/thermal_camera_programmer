# HM-TM5X Thermal Camera Programmer

This application allows the user to change the settings of their HM-TM5X Thermal Camera. This camera can be found on AliExpress as well as drone retailers like Axis Flying and others. The camera used when developing this is the one with 3 PCBs in the stack.

[The PDF](UDNHM-TM5X-XRGCUARTCVBSCommunicationProtocolGuide.pdf) with the serial communication protocol are included in the repo.

The repo includes an executable application which was built with `pyinstaller '.\HM-TM5X Thermal Camera Programmer.spec'` which was written with [this guide](https://www.pythonguis.com/tutorials/packaging-pyqt5-pyside2-applications-windows-pyinstaller/).

## Using the Application

To use the application, your thermal camera will need to be powered and preferably connected to a screen to see the changes.

In order to program the device, you will need to use a USB-to-Serial Adapter, which will have a USB plug on one side and a few pins on the other (VCC, GND, RX, and TX).
These can be found on Amazon for a few bucks and will be called either a USB to TTL Serial Adapter or Converter. It should also have some way to change the output voltage between 5V and 3.3V.

_**Make sure you have it set to 3.3V**_ or you risk wrecking the UART control on your thermal camera. 

Wiring up the adapter to the thermal camera is simple: connect the TX (pin 4) to your adapters RX pin and the RX (pin 5) to your adapters TX pin. Again, make sure that your adapter is set to 3.3V operation.

Once the device is correctly wired up, open the application (or run `main.py` using python 3.10, though you may need to install some libraries).

Once in the application, select your adapters port using the `Port Select` menu. If you don't know which port your adapter is on, google how to figure that out.

As a first test, click `Get Model Name`. The window will show the bytestring that is sent to the device, indicated by `>> 0x<bytestring>` and then will display the response.

This is as far as I've gotten in the testing of the program, so I hope it responds correctly :)