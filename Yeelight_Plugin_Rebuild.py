import json
import threading
import time
import requests
import webbrowser
from yeelight import discover_bulbs
from yeelight import Bulb
from yeelight import PowerMode
from tkinter import *
import TouchPortalAPI as TP


'''

Touch Portal Yeelight plugin

'''

try:
    permIps = []
    with open("Permanent_Ips.json") as jsonFile:
        for i in json.load(jsonFile):
            permIps.append(i)
except:
    permIps = []

Running = True

settings = {}


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




def updateCheck():
    """
    This Function is for checking updates on github
    """
    WriteServerData(f"Checking for updates")
    try:
        CheckingUpdateFile = requests.get("https://api.github.com/repos/ElyOshri/Touch-Portal-Yeelight-Plugin/tags", {"User-Agent": "Yeelight Plugin"}).json()
        # Todo: Change to new version
        if str(CheckingUpdateFile[0]['name']) != "v1.3":
            WriteServerData(f"Found an updated, version: {CheckingUpdateFile[0]['name']}")
            WriteServerData("New version is available please update")
            webbrowser.get().open_new_tab(f"https://github.com/ElyOshri/Touch-Portal-Yeelight-Plugin/releases/tag/{CheckingUpdateFile[0]['name']}")
        else:
            WriteServerData(f"No new version is available")
    except:
        WriteServerData("User Passed Update Check Rate Limit")


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
        DeviceList = []
        for i in permIps:
            DeviceList.append(i)
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
                WriteServerData(f'Found New Device {x} creating a variable for it')
                state = [
                    {"id": f"TPPlugin.Yeelight.device.{x}CurrentBrightness", "desc": f"YeeLight {x} Brightness", "value": "0"},
                    {"id": f"TPPlugin.Yeelight.device.{x}power", "desc": f"YeeLight {x} ON or OFF", "value": "0"},
                    {"id": f"TPPlugin.Yeelight.device.{x}hue", "desc": f"YeeLight {x} Hue", "value": "0"},
                    {"id": f"TPPlugin.Yeelight.device.{x}rgb", "desc": f"YeeLight {x} RGB", "value": "0"}
                ]

                TPClient.createStateMany(state)

                if x not in OLD_DeviceList:
                    OLD_DeviceList.append(x)

                TPClient.choiceUpdate("TPPlugin.YeeLight.Actions.OnOFFTigger.Data.DeviceList", DeviceList)  # update the list when theres a new

            if settings[2]["Enable Disconnected Devices"] == "Off":
                for j in OLD_DeviceList:
                    if j not in DeviceList:
                        WriteServerData(f'Removing {j} from the update states')
                        state = ["TPPlugin.Yeelight.device." + j + "CurrentBrightness", "TPPlugin.Yeelight.device." + j + "power", "TPPlugin.Yeelight.device." + j + "hue", "TPPlugin.Yeelight.device." + j + "rgb"]
                        TPClient.removeStateMany(state)

                        OLD_DeviceList.remove(j)
                        TPClient.choiceUpdate("TPPlugin.YeeLight.Actions.OnOFFTigger.Data.DeviceList", OLD_DeviceList)

        if oldState != DeviceState and DeviceState != []:
            for x in DeviceState:
                if x not in oldState:
                    hue = "Hue Is Not Available"
                    if list(x.values())[0][0]['hue'] != None:
                        hue = int(list(x.values())[0][0]['hue'])
                    rgb = "RGB Is Not Available"
                    if list(x.values())[0][0]['rgb'] != None:
                        rgb = DecimalToHex(int(list(x.values())[0][0]['rgb']))

                    state = [{'id': "TPPlugin.Yeelight.device." + list(x)[0] + "CurrentBrightness",
                              'value': str(int(list(x.values())[0][0]['current_brightness']))},
                             {'id': "TPPlugin.Yeelight.device." + list(x)[0] + "power",
                              'value': str(list(x.values())[0][0]['power'])},
                             {'id': "TPPlugin.Yeelight.device." + list(x)[0] + "hue", 'value': str(hue)},
                             {'id': "TPPlugin.Yeelight.device." + list(x)[0] + "rgb", 'value': str(rgb)}]

                    TPClient.stateUpdateMany(state)

                    TPClient.connectorUpdate(f"TPPlugin.YeeLight.Connectors.Brightness|TPPlugin.YeeLight.Actions.OnOFFTigger.Data.DeviceList={list(x)[0]}", int(list(x.values())[0][0]['current_brightness']))
            oldState = DeviceState
    else:
        timer.cancel()


try:
    TPClient = TP.Client("TPYeeLight", autoClose=True, updateStatesOnBroadcast=True)
except Exception as e:
    sys.exit(f"Could not create TP Client, exiting. Error was:\n{repr(e)}")


@TPClient.on(TP.TYPES.onConnect)
def onConnect(data):
    global settings
    settings = data.get('settings')
    WriteServerData(f"Connected to TP v{data.get('tpVersionString', '?')}, plugin v{data.get('pluginVersion', '?')}.")
    WriteServerData(f"Settings: {data['settings']}")
    if settings[5]['Enable Auto Update'] == 'On':
        updateCheck()
    if settings[3]["Permanent Devices UI"] == "On":
        threading.Thread(target=StartUI).start()
    updateStates()


@TPClient.on(TP.TYPES.onSettingUpdate)
def onSettingUpdate(d):
    WriteServerData(d)
    global settings
    if settings[3]["Permanent Devices UI"] != d['values'][3]["Permanent Devices UI"] and d['values'][3]["Permanent Devices UI"] == "On":
        threading.Thread(target=StartUI).start()
    settings = d['values']


@TPClient.on(TP.TYPES.onAction)
def onAction(d):
    WriteServerData(f"Received: {d}")
    try:
        if d['data'][0]['value'] != "" and d['data'][1]['value'] != "":
            try:
                if d['actionId'] == "TPPlugin.YeeLight.Actions.OnOFFTigger":
                    if d['data'][0]['value'] == "ON":
                        WriteServerData(f"Running Action Turn On {d['data'][0]['value']} Light")
                        Bulb(d['data'][1]['value']).turn_on()
                        return

                    elif d['data'][0]['value'] == "OFF":
                        WriteServerData(f"Running Action Turn Off {d['data'][0]['value']} Light")
                        Bulb(d['data'][1]['value']).turn_off()
                        return

                if d['actionId'] == "TPPlugin.YeeLight.Actions.Bright" and d['data'][1]['id'] == "TPPlugin.YeeLight.Actions.DataBright":
                    WriteServerData(f"Running Action Bright Level {d['data'][0]['value']} On {d['data'][1]['value']}")
                    Bulb(d['data'][0]['value'], auto_on=True).set_brightness(int(d['data'][1]['value']))
                    return

                if d['actionId'] == 'TPPlugin.YeeLight.Actions.Temp' and d['data'][1]['id'] == 'TPPlugin.YeeLight.Actions.DataTemp':
                    WriteServerData(f"Running Action Temp Level {d['data'][0]['value']} On {d['data'][1]['value']}")
                    Bulb(d['data'][0]['value'], auto_on=True).set_color_temp(int(d['data'][1]['value']))
                    return

                if d['actionId'] == "TPPlugin.YeeLight.Actions.RGB" and d['type'] == "action":
                    test = d['data'][1]['value'].lstrip('#')
                    RGB = list(int(test[i:i + 2], 16) for i in (0, 2, 4))
                    WriteServerData(f"Running Converting Hex: {d['data'][1]['value']} to RGB:{RGB}")
                    print(f"RGB = {RGB}")
                    Bulb(d['data'][0]['value']).set_rgb(RGB[0], RGB[1], RGB[2])
                    return

                if d['actionId'] == 'TPPlugin.YeeLight.Actions.Toggle' and d['data'][1]['id'] == 'TPPlugin.YeeLight.Actions.UnusedData':
                    WriteServerData(f"Running Action Toggle {d['data'][0]['value']} Light")
                    Bulb(d['data'][0]['value']).toggle()
                    return

                if d['actionId'] == 'TPPlugin.YeeLight.Actions.Brightness_Down' and d['data'][1]['id'] == "TPPlugin.YeeLight.Actions.DataBrightDown":
                    WriteServerData(f"Running Action Brightness Down {d['data'][0]['value']} Light")
                    BrightDown = Bulb(d['data'][0]['value']).get_properties(requested_properties=['bright'])
                    Bulb(d['data'][0]['value'], auto_on=True).set_brightness(int(BrightDown['bright']) - int(d['data'][1]['value']))
                    return

                if d['actionId'] == 'TPPlugin.YeeLight.Actions.Brightness_Up' and d['data'][1]['id'] == "TPPlugin.YeeLight.Actions.DataBrightUp":
                    WriteServerData(f"Running Action Brightness Up {d['data'][0]['value']} Light")
                    BrightUp = Bulb(d['data'][0]['value']).get_properties(requested_properties=['bright'])
                    Bulb(d['data'][0]['value'], auto_on=True).set_brightness(int(BrightUp['bright']) + int(d['data'][1]['value']))
                    return

                if d['actionId'] == 'TPPlugin.YeeLight.Actions.LightMode' and d['data'][1]['id'] == "TPPlugin.YeeLight.Actions.DataLightMode":
                    if d['data'][1]['value'] == "LAST":
                        Bulb(d['data'][0]['value']).set_power_mode(PowerMode.LAST)
                    elif d['data'][1]['value'] == "NORMAL":
                        Bulb(d['data'][0]['value']).set_power_mode(PowerMode.NORMAL)
                    elif d['data'][1]['value'] == "RGB":
                        Bulb(d['data'][0]['value']).set_power_mode(PowerMode.RGB)
                    elif d['data'][1]['value'] == "HSV":
                        Bulb(d['data'][0]['value']).set_power_mode(PowerMode.HSV)
                    elif d['data'][1]['value'] == "COLOR_FLOW":
                        Bulb(d['data'][0]['value']).set_power_mode(PowerMode.COLOR_FLOW)
                    elif d['data'][1]['value'] == "MOONLIGHT":
                        Bulb(d['data'][0]['value']).set_power_mode(PowerMode.MOONLIGHT)
                    return

                return
            except:
                WriteServerData(f"User Passed Connection Rate Limit")
    except KeyError:
        WriteServerData('User did not input values')


@TPClient.on(TP.TYPES.onConnectorChange)
def connectors(d):
    if d['connectorId'] == 'TPPlugin.YeeLight.Connectors.Brightness':
        try:
            WriteServerData(f"Setting {d['data'][0]['value']} brightness to {d['value']}")
            Bulb(d['data'][0]['value']).set_brightness(d['value'])
        except:
            WriteServerData("User Passed Connection Rate Limit")


@TPClient.on(TP.TYPES.onListChange)
def lists(d):
    if d['actionId'] == 'TPPlugin.YeeLight.Actions.LightMode' and 'value' in list(d):
        prop = Bulb(d['value']).get_properties(requested_properties=['ct', 'rgb', 'hue'])
        state = ["LAST"]
        if prop['ct'] != None:
            state.append("NORMAL")
        if prop['rgb'] != None:
            state.append("RGB")
        if prop['hue'] != None:
            state.append('HSV')
            state.append('COLOR_FLOW')
        if prop['ct'] != None:
            state.append("MOONLIGHT")
        TPClient.choiceUpdate('TPPlugin.YeeLight.Actions.DataLightMode', state)


@TPClient.on(TP.TYPES.onShutdown)
def onShutdown(data):
    WriteServerData(f"Shutdown TPYeeLightPlugin...")
    WriteServerData(data)
    global Running
    Running = False
    TPClient.disconnect()


TPClient.connect()

import sys
sys.exit()
