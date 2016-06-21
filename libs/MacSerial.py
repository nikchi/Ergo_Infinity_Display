import usb1

SERIAL_INTERFACE = 3
SERIAL_OUT = SERIAL_INTERFACE + 1

class MacSerial(object):
    def __init__(self):
        self.open()

    def open(self):
        self.context = usb1.USBContext()
        self.device = self.getErgodoxDevice()
        self.conn = self.device.open()
        self.conn.claimInterface(SERIAL_INTERFACE)

    def close(self):
        self.conn.releaseInterface(SERIAL_INTERFACE)
        self.device.close()

    def getErgodoxDevice(self):
        devices = self.context.getDeviceList()
        ergo = None
        for device in devices:
            manufacturer = device.getManufacturer()
            if manufacturer and 'Kiibohd' in manufacturer:
                return device
        return None

    def write(self, command):
        self.conn.bulkWrite(SERIAL_OUT, command)

