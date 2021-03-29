import socket
import json
import threading
import time
import sys
import requests
import webbrowser
import os
from yeelight import discover_bulbs
from yeelight import Bulb

'''

Touch Portal Yeelight plugin

'''

TPHOST = '127.0.0.1'
TPPORT = 12136

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


s.connect((TPHOST, TPPORT))
s.sendall(b'{"type":"pair","id":"TPYeeLight"}\n')
data = s.recv(1024)
print(repr(data))
settings = (json.loads(data.decode('utf-8')))["settings"]


Running = True



def DecimalToHex(c):
    b = c % 256
    g_0 = (c % 65536 - b)
    r_0 = c - g_0 - b
    g = g_0 / 256
    r = r_0 / 65536
    return '#ff%02x%02x%02x' % (int(r), int(g), int(b))


def WriteServerData(Serverinfo):
    '''
    This Function makes it eazier for write a log without repeating it
    '''
    if settings[3]["Enable Log"] == 'On':
        currenttime = (time.strftime('[%I:%M:%S:%p] '))
        logfile = open('log.txt', 'a')
        logfile.write(currenttime + "%s" % (Serverinfo))
        logfile.write('\n')
        logfile.close()
    elif settings[3]["Enable Log"] == 'Off':
        print(Serverinfo)

if settings[4]["Enable Auto Update"] == "On":
    WriteServerData(f"Checking for updates")
    CheckingUpdateFile = requests.get("https://api.github.com/repos/ElyOshri/Touch-Portal-yeelight-Plugin/tags").json()
    if str(CheckingUpdateFile[0]['name']) != "v1.2.1":
        WriteServerData(f"Found a updated version: {CheckingUpdateFile[0]['name']}")
        WriteServerData("New version is availble please update")
        webbrowser.get().open_new_tab('https://github.com/ElyOshri/Touch-Portal-Yeelight-Plugin/releases')
    if str(CheckingUpdateFile[0]['name']) == "v1.2.1":
        WriteServerData(f"No new verison is available")

OLD_DeviceList = []


def updatestates():
    '''
    This Function for sending data to TouchPortal, Creating new var and removing
    '''
    global OLD_DeviceList
    timer = threading.Timer(int(settings[0]["State Update Delay"]), updatestates)
    timer.start()
    if Running:
        DeviceList = []
        DeviceState = []
        try:
            for i in discover_bulbs(int(settings[1]["Discover Devices Delay"])):
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
                print(f'Found New Device {x} creating a variaible for it')
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


        for x in DeviceState:
            s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "CurrentBrightness", int(list(x.values())[0][0]['current_brightness']))).encode())
            s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "power",list(x.values())[0][0]['power'])).encode())
            if list(x.values())[0][0]['hue'] != None:
                s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "hue", int(list(x.values())[0][0]['hue']))).encode())
            elif list(x.values())[0][0]['hue'] == None:
                s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "hue", "Hue Is Not Available")).encode())
            if list(x.values())[0][0]['rgb'] != None:
                s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "rgb", DecimalToHex(int(list(x.values())[0][0]['rgb'])))).encode())
            elif list(x.values())[0][0]['rgb'] == None:
                s.sendall(('{"type":"stateUpdate", "id":"%s", "value":"%s"}\n' % ("TPPlugin.Yeelight.device." + list(x)[0] + "rgb", "RGB Is Not Available")).encode())
    else:
        timer.cancel()


updatestates()


while Running:
    '''
    This Keeps this running and wait until it receive a data
    '''
    try:
        CHUNK_SIZE = 4000
        buffer = bytearray()
        data = s.recv(CHUNK_SIZE)
        buffer.extend(data)
    except ConnectionResetError:
        WriteServerData(f"Shutdown TPYeeLightPlugin...")
        Running = False
        sys.exit()


    firstline = buffer[:buffer.find(b'\n')]
    print(firstline)
    WriteServerData(f"Reviced: {firstline}")
    d = firstline
    d = json.loads(d)
    if d['type'] == "closePlugin":
        WriteServerData(f"Shutdown TPYeeLightPlugin...")
        Running = False
        sys.exit()

    if d['type'] == 'settings':
        settings[0]['State Update Delay'] = d['values'][0]['State Update Delay']
        settings[1]["Discover Devices Delay"] = d['values'][1]['Discover Devices Delay']
        settings[2]["Enable Disconnected Devices"] = d['values'][2]['Enable Disconnected Devices']
        settings[3]["Enable Log"] = d['values'][3]['Enable Log']
        settings[4]["Enable Auto Update"] = d['values'][4]['Enable Auto Update']

    if d['type'] != 'closePlugin' and Running and d['type'] != 'listChange' and d['type'] != "settings" and d['type'] != "broadcast":
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
                        WriteServerData(f"Running Action Bright Level {d['data'][0]['value']} On {d['data'][1]['value']}")
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
                        Bulb(d['data'][0]['value'], auto_on=True).set_brightness(int(BrightDown['bright'])-int(d['data'][1]['value']))

                    if d['actionId'] == 'TPPlugin.YeeLight.Actions.Brightness_Up' and d['data'][1]['id'] == "TPPlugin.YeeLight.Actions.DataBrightUp":
                        WriteServerData(f"Running Action Brightness Up {d['data'][0]['value']} Light")
                        BrightUp = Bulb(d['data'][0]['value']).get_properties(requested_properties=['bright'])
                        Bulb(d['data'][0]['value'], auto_on=True).set_brightness(int(BrightUp['bright'])+int(d['data'][1]['value']))
                except:
                    WriteServerData(f"User Passed Connection Rate Limit")
        except KeyError:
            print('User did not input values')



