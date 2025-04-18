import time
from bluepy.btle import Peripheral, UUID
from bluepy.btle import Scanner, DefaultDelegate
import struct

AUTO_CONNECT = True
TARGET_SVC_UUID = 0x0000

class NotificationDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        values = struct.unpack('<4h', data[0:8]);
        print(values[1:])

def find_addr(auto_connect, target_svc_uuid):
    target_svc_uuid_str = hex(target_svc_uuid)[2:]

    scanner = Scanner()
    devices = scanner.scan(3.0)

    addr = ""

    if not auto_connect:
        addrs = []
        num = 0
        for dev in devices:
            addrs.append(dev.addr)
            print("="*20)
            print(num)
            print(f"Device {dev.addr}({dev.addrType}), RSSI={dev.rssi} dB")
            for (adtype, desc, value) in dev.getScanData():
                print(f"{desc} = {value}")
                if "BlueNRG" in value:
                    print('*'*50)
            addr = dev.addr
            print("="*20)
            num += 1
        num = input("Number:")
        num = int(num)
        addr = addrs[num]

    else:
        for dev in devices:
            show = False
            for (adtype, desc, value) in dev.getScanData():
                if "BlueNRG" in value:
                    show = True

            if show:
                print("="*20)
                print(f"Device {dev.addr}({dev.addrType}), RSSI={dev.rssi} dB")
                for (adtype, desc, value) in dev.getScanData():
                    print(f"{desc} = {value}")
                addr = dev.addr
                print("="*20)
                break

    return addr

def controlCCCDNotification(ch, switch_on):
    if switch_on:
        target = b"\x01\x00"
    else:
        target = b"\x00\x00"

    cccd = ch.getDescriptors(forUUID=0x2902)

    if len(cccd) == 0:
        print("No CCCD descriptor")
    else:
        print("================ Change CCCD value =========================")
        print("CCCD: ", cccd[0])

        value = cccd[0].read()
        print("CCCD original value:", value)

        print(f"Write", target, 'to CCCD')
        cccd[0].write(target)
        time.sleep(0.5)

        print('CCCD new value:', cccd[0].read())
        print("============================================================")



if __name__ == '__main__':
    addr = find_addr(AUTO_CONNECT, TARGET_SVC_UUID)
    print(f"addr:{addr}.")

    if addr != "":
        dev = Peripheral(addr, 'random')
        dev.setDelegate(NotificationDelegate())

        svc = dev.getServiceByUUID("00000000-0001-11e1-9ab4-0002a5d5c51b")
        print ("Service: ", str(svc), svc.uuid)

        for ch in svc.getCharacteristics():
            print(ch, ch.uuid)

        ch = svc.getCharacteristics(forUUID="00e00000-0001-11e1-ac36-0002a5d5c51b")[0]
        controlCCCDNotification(ch, True)

        freq_ch = svc.getCharacteristics(forUUID="00e00000-0002-11e1-ac36-0002a5d5c51b")[0]
        print(f"== freq", freq_ch.read())

        counter = 0
        while True:
            if counter == 5:
                controlCCCDNotification(ch, False)
            elif counter == 10:
                controlCCCDNotification(ch, True)
            elif counter == 15:
                print("Write ", 0x14)
                print(freq_ch)
                num = 50
                num = num.to_bytes(2, byteorder='little')
                print("== num: ", num)
                freq_ch.write(num, withResponse=True)

                print(f"== freq", freq_ch.read())
            elif counter == 50:
                print("Write ", 0x14)
                print(freq_ch)
                num = 5
                num = num.to_bytes(2, byteorder='little')
                print("== num: ", num)
                freq_ch.write(num, withResponse=True)

                print(f"== freq", freq_ch.read())

            counter += 1

            if dev.waitForNotifications(1.0):
                continue

        dev.disconnect()
        time.sleep(1)