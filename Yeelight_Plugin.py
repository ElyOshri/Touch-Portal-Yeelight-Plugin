import socket
import json
import threading
import time
import sys
import requests
import webbrowser
from yeelight import discover_bulbs
from yeelight import Bulb
from tkinter import *


'''

Touch Portal Yeelight plugin

'''


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(('127.0.0.1', 12136))
s.sendall(b'{"type":"pair","id":"TPYeeLight"}\n')
data = s.recv(1024)
print(repr(data))
settings = (json.loads(data.decode('utf-8')))["settings"]

try:
    permIps = []
    with open("Permanent_Ips.json") as jsonFile:
        for i in json.load(jsonFile):
            permIps.append(i)
except:
    permIps = []


Running = True


def DecimalToHex(c):
    b = c % 256
    g_0 = (c % 65536 - b)
    r_0 = c - g_0 - b
    g = g_0 / 256
    r = r_0 / 65536
    return '#ff%02x%02x%02x' % (int(r), int(g), int(b))


def WriteServerData(ServerInfo):
    """
    This Function makes it easier for write a log without repeating it
    """
    if settings[4]["Enable Log"] == 'On':
        currentTime = (time.strftime('[%I:%M:%S:%p] '))
        logfile = open('log.txt', 'a')
        logfile.write(currentTime + "%s" % ServerInfo)
        logfile.write('\n')
        logfile.close()
    elif settings[4]["Enable Log"] == 'Off':
        print(ServerInfo)


def StartUI():
    root = Tk()
    root.title("Yeelight - Permanent Ips")
    root.geometry("250x350")
    root.iconphoto(True, PhotoImage(file="icon.png"))

    myListBox = Listbox(root, width=20)
    myListBox.config(font=("Ariel", 11), justify="center")
    myListBox.pack(pady=15, padx=15)
    global permIps
    for ip in permIps:
        myListBox.insert(0, ip)

    def delete():
        global permIps
        WriteServerData(f"Deleting {myListBox.get(ANCHOR)} From Perm Devices")
        myListBox.delete(ANCHOR)
        permIps = []
        for ip in myListBox.get(0, END):
            permIps.append(ip)
        with open("Permanent_Ips.json", "w") as jsonFile:
            json.dump(permIps, jsonFile)

    def addIp():
        global permIps
        WriteServerData(f"Adding {text.get()} To Perm Devices")
        myListBox.insert(0, text.get())
        permIps = []
        for ip in myListBox.get(0, END):
            permIps.append(ip)
        with open("Permanent_Ips.json", "w") as jsonFile:
            json.dump(permIps, jsonFile)

    def helpButton():
        webbrowser.get().open_new_tab("https://github.com/ElyOshri/Touch-Portal-Yeelight-Plugin#permanent-devices-tutorial")

    Button(root, text="Delete", command=delete).pack(pady=0)
    Button(root, text="Add New Device", command=addIp).pack(pady=5)
    Button(root, text="?", command=helpButton, bg="gray", fg="white", font=("Ariel", 10)).pack(pady=5, padx=(5, 225), side=BOTTOM)
    text = StringVar(root, value="Enter Device Ip Here")
    Entry(root, textvariable=text, justify="center").pack(pady=5)

    root.mainloop()


if settings[5]["Enable Auto Update"] == "On":
    """
    This Function is for checking updates on github
    """
    WriteServerData(f"Checking for updates")
    try:
        CheckingUpdateFile = requests.get("https://api.github.com/repos/ElyOshri/Touch-Portal-Yeelight-Plugin/tags", {"User-Agent": "Yeelight Plugin"}).json()
        if str(CheckingUpdateFile[0]['name']) != "v1.3":  #Todo: Change to new version
            WriteServerData(f"Found a updated version: {CheckingUpdateFile[0]['name']}")
            WriteServerData("New version is available please update")
            webbrowser.get().open_new_tab(f"https://github.com/ElyOshri/Touch-Portal-Yeelight-Plugin/releases/tag/{CheckingUpdateFile[0]['name']}")
        else:
            WriteServerData(f"No new version is available")
    except:
        WriteServerData("User Passed Update Check Rate Limit")

if settings[3]["Permanent Devices UI"] == "On":
    threading.Thread(target=StartUI).start()

OLD_DeviceList = []
oldState = []
timer = threading.Timer


def updateStates():
    """
    This Function for sending data to TouchPortal and searching for new Devices
    """
    global OLD_DeviceList
    global oldState
    global timer
    timer = threading.Timer(int(settings[0]["State Update Delay"]), updateStates)
    timer.start()
    if Running:
        DeviceList = permIps
        DeviceState = []
        try:
            for i in discover_bulbs(int(settings[1]["Discover Devices Delay"])):
                if i["ip"] not in DeviceList:
                    DeviceList.append(i['ip'])
        except:
            pass
        try:
            for i in range(len(DeviceList)):
                DeviceState.append({DeviceList[i]: [Bulb(DeviceList[i]).get_properties(requested_properties=['power', 'bright', 'rgb', 'hue', 'color_mode'])]})
        except:
            pass
        for x in DeviceList:
            if x not in OLD_DeviceList:
                print(f'Found New Device {x} creating a variable for it')
                s.sendall(('{"type":"createState", "id":"%s", "desc":"YeeLight %s Brightness", "defaultValue":"0"}\n' % ("TPPlugin.Yeelight.device." + x + "CurrentBrightness", x)).encode())
                s.sendall(('{"type":"createState", "id":"%s", "desc":"YeeLight %s ON or OFF", "defaultValue":"0"}\n' % ("TPPlugin.Yeelight.device." + x + "power", x)).encode())
                s.sendall(('{"type":"createState", "id":"%s", "desc":"YeeLight %s Hue", "defaultValue":"0"}\n' % ("TPPlugin.Yeelight.device." + x + "hue", x)).encode())
                s.sendall(('{"type":"createState", "id":"%s", "desc":"YeeLight %s RGB", "defaultValue":"0"}\n' % ("TPPlugin.Yeelight.device." + x + "rgb", x)).encode())

                if x not in OLD_DeviceList:
                    OLD_DeviceList.append(x)

                print(OLD_DeviceList)
                s.sendall(('{"type":"choiceUpdate", "id":"TPPlugin.YeeLight.Actions.OnOFFTigger.Data.DeviceList", "value":%s}\n' % DeviceList).encode())  # update the list when theres a new Device
            if settings[2]["Enable Disconnected Devices"] == "Off":
                for j in OLD_DeviceList:
                    if j not in DeviceList:
                        print(f'Removing {j} from the update states')
                        s.sendall(('{"type":"removeState", "id":"%s", "desc":"YeeLight %s Brightness", "defaultValue":"0"}\n' % ("TPPlugin.Yeelight.device." + j + "CurrentBrightness", j)).encode())
                        s.sendall(('{"type":"removeState", "id":"%s", "desc":"YeeLight %s ON Or OFF", "defaultValue":"0"}\n' % ("TPPlugin.Yeelight.device." + j + "power", j)).encode())
                        s.sendall(('{"type":"removeState", "id":"%s", "desc":"YeeLight %s Hue", "defaultValue":"0"}\n' % ("TPPlugin.Yeelight.device." + j + "hue", j)).encode())
                        s.sendall(('{"type":"removeState", "id":"%s", "desc":"YeeLight %s RGB", "defaultValue":"0"}\n' % ("TPPlugin.Yeelight.device." + j + "rgb", j)).encode())

                        OLD_DeviceList.remove(j)

        if oldState != DeviceState and DeviceState != []:
            for x in DeviceState:
                if x not in oldState:
                    s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "CurrentBrightness", int(list(x.values())[0][0]['current_brightness']))).encode())
                    s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "power", list(x.values())[0][0]['power'])).encode())
                    if list(x.values())[0][0]['hue'] != None:
                        s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "hue", int(list(x.values())[0][0]['hue']))).encode())
                    elif list(x.values())[0][0]['hue'] == None:
                        s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "hue", "Hue Is Not Available")).encode())
                    if list(x.values())[0][0]['rgb'] != None:
                        s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "rgb", DecimalToHex(int(list(x.values())[0][0]['rgb'])))).encode())
                    elif list(x.values())[0][0]['rgb'] == None:
                        s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "rgb", "RGB Is Not Available")).encode())
            oldState = DeviceState
    else:
        timer.cancel()


updateStates()

while Running:
    '''
    This Keeps this running and wait until it receive a data
    '''
    try:
        buffer = bytearray()
        while True:
            data = s.recv(1)
            if data != b'\n':
                buffer.extend(data)
            else:
                break
    except ConnectionResetError:
        WriteServerData(f"Shutdown TPYeeLightPlugin...")
        Running = False
        timer.cancel()
        sys.exit()

    firstLine = buffer[:buffer.find(b'\n')]
    print(firstLine)
    WriteServerData(f"Received: {firstLine}")
    d = firstLine
    d = json.loads(d)
    if d['type'] == "closePlugin":
        WriteServerData(f"Shutdown TPYeeLightPlugin...")
        Running = False
        timer.cancel()
        sys.exit()

    if d['type'] == 'settings':
        settings[0]['State Update Delay'] = d['values'][0]['State Update Delay']
        settings[1]["Discover Devices Delay"] = d['values'][1]['Discover Devices Delay']
        settings[2]["Enable Disconnected Devices"] = d['values'][2]['Enable Disconnected Devices']
        if settings[3]["Permanent Devices UI"] != d['values'][3]["Permanent Devices UI"] and d['values'][3]["Permanent Devices UI"] == "On":
            threading.Thread(target=StartUI).start()
        settings[3]["Permanent Devices UI"] = d['values'][3]["Permanent Devices UI"]
        settings[4]["Enable Log"] = d['values'][4]['Enable Log']
        settings[5]["Enable Auto Update"] = d['values'][5]['Enable Auto Update']

    if Running and d['type'] == "action":
        try:
            if d['data'][0]['value'] != "" and d['data'][1]['value'] != "":
                try:
                    if d['data'][0]['value'] == "ON":
                        WriteServerData(f"Running Action Turn On {d['data'][0]['value']} Light")
                        Bulb(d['data'][1]['value']).turn_on()

                    elif d['data'][0]['value'] == "OFF":
                        WriteServerData(f"Running Action Turn Off {d['data'][0]['value']} Light")
                        Bulb(d['data'][1]['value']).turn_off()

                    if d['actionId'] == "TPPlugin.YeeLight.Actions.Bright" and d['data'][1]['id'] == "TPPlugin.YeeLight.Actions.DataBright":
                        WriteServerData(
                            f"Running Action Bright Level {d['data'][0]['value']} On {d['data'][1]['value']}")
                        Bulb(d['data'][0]['value'], auto_on=True).set_brightness(int(d['data'][1]['value']))

                    if d['actionId'] == 'TPPlugin.YeeLight.Actions.Temp' and d['data'][1]['id'] == 'TPPlugin.YeeLight.Actions.DataTemp':
                        WriteServerData(f"Running Action Temp Level {d['data'][0]['value']} On {d['data'][1]['value']}")
                        Bulb(d['data'][0]['value'], auto_on=True).set_color_temp(int(d['data'][1]['value']))

                    if d['actionId'] == "TPPlugin.YeeLight.Actions.RGB" and d['type'] == "action":
                        test = d['data'][1]['value'].lstrip('#')
                        RGB = list(int(test[i:i + 2], 16) for i in (0, 2, 4))
                        WriteServerData(f"Running Converting Hex: {d['data'][1]['value']} to RGB:{RGB}")
                        print(f"RGB = {RGB}")
                        Bulb(d['data'][0]['value']).set_rgb(RGB[0], RGB[1], RGB[2])

                    if d['actionId'] == 'TPPlugin.YeeLight.Actions.Toggle' and d['data'][1]['id'] == 'TPPlugin.YeeLight.Actions.UnusedData':
                        WriteServerData(f"Running Action Toggle {d['data'][0]['value']} Light")
                        Bulb(d['data'][0]['value']).toggle()

                    if d['actionId'] == 'TPPlugin.YeeLight.Actions.Brightness_Down' and d['data'][1]['id'] == "TPPlugin.YeeLight.Actions.DataBrightDown":
                        WriteServerData(f"Running Action Brightness Down {d['data'][0]['value']} Light")
                        BrightDown = Bulb(d['data'][0]['value']).get_properties(requested_properties=['bright'])
                        Bulb(d['data'][0]['value'], auto_on=True).set_brightness(
                            int(BrightDown['bright']) - int(d['data'][1]['value']))

                    if d['actionId'] == 'TPPlugin.YeeLight.Actions.Brightness_Up' and d['data'][1]['id'] == "TPPlugin.YeeLight.Actions.DataBrightUp":
                        WriteServerData(f"Running Action Brightness Up {d['data'][0]['value']} Light")
                        BrightUp = Bulb(d['data'][0]['value']).get_properties(requested_properties=['bright'])
                        Bulb(d['data'][0]['value'], auto_on=True).set_brightness(
                            int(BrightUp['bright']) + int(d['data'][1]['value']))
                except:
                    WriteServerData(f"User Passed Connection Rate Limit")
        except KeyError:
            print('User did not input values')
