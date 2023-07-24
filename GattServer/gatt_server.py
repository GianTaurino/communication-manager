#!/usr/bin/python3

import dbus
import json
import datetime

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor


GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 4000 # 1min = 60000

class DangerAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Machine 1")
        self.include_tx_power = True

class DangerService(Service):
    DANGER_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        self.farenheit = True

        Service.__init__(self, index, self.DANGER_SVC_UUID, True)
        self.add_characteristic(DangerCharacteristic(self))

class DangerCharacteristic(Characteristic):
    DANGER_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.DANGER_CHARACTERISTIC_UUID,
                ["notify"], service)
        self.add_descriptor(DangerDescriptor(self))

    def get_danger_detection(self):
        with open('detection.json', 'r') as f:
            detection = json.load(f)
        det_date = detection["date-time"]
        det_date = det_date[:len(det_date)-1]
        now = datetime.datetime.utcnow()

        diff = (now - det_date).seconds
        print ("diff: ", diff)
        if diff < 3 :
            strDang = "Danger: " + detection["uuid"]
            print ("strDang: ", strDang)
            return strDang
            value = []
            
            for c in strDang:
            	value.append(dbus.Byte(c.encode()))

        return "Null"


    def set_detection_callback(self):
        if self.notifying:
            strDang = self.get_danger_detection()

            if not strDang == "Null":
                value = []
                for c in strDang:
                    value.append(dbus.Byte(c.encode()))
                self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
                print("Notified")

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_danger_detection()

        print("Start Notify")
        # self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_detection_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_danger_detection()

        return value

class DangerDescriptor(Descriptor):
    DANG_DESCRIPTOR_UUID = "00000003-710e-4a5b-8d75-3e5b444bc3cf"
    DANG_DESCRIPTOR_VALUE = "Beacon detected"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.DANG_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.DANG_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

app = Application()
app.add_service(DangerService(0))
app.register()

adv = DangerAdvertisement(0)
adv.register()

try:
    app.run()
    DangerCharacteristic.StartNotify()
except KeyboardInterrupt:
    app.quit()
