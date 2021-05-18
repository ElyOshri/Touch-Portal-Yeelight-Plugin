# Touch-Portal-Yeelight-Plugin
A Yeelight plugin for Touch Portal by: Killer_BOSS and ElyOshri

[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/ElyOshri/Touch-Portal-Yeelight-Plugin?include_prereleases&label=Release)](https://github.com/ElyOshri/Touch-Portal-Yeelight-Plugin/releases/tag/v1.2.1)
[![Downloads](https://img.shields.io/github/downloads/ElyOshri/Touch-Portal-Yeelight-Plugin/total?label=Downloads)](https://github.com/ElyOshri/Touch-Portal-Yeelight-Plugin/releases)
[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.me/ElyOshri1)

## Overview

This plugin is for controlling Yeelight devices in your local network

## Features

* Discovers devices in the network automatically.
* Changing device state, color and brightness thru buttons.
* Allows button state and event changes in real time from the device.

## Installation Guide

Go to the releases:
https://github.com/ElyOshri/Touch-Portal-Yeelight-Plugin/releases

Get the latest version and there will be a TPP file you can download. From Touch Portal go to Import Plugin. Once you have done that restart Touch Portal. After that you will have a list of new actions you can choose from. Also "Dynamic Text" variables are available. You can see them from the Dynamic Text Updater, or you can add an option for "On Plugin State Change" then select the corresponding state and "Changes to". 

For Device ON or OFF state you need to use "on" or "off".

For RGB background color change or text color change you can use "When Plug-in State changes" and set it to "does not change to" and it the text you need to put "00000000" for it to work.

For Temp change you can use any number between 1700 and 6500 and depending on your device it should work

If non of the devices show up in Touch Portal make sure that Lan Control is enabled in the Yeelight app, This link should help to turn it on: https://getyeti.webflow.io/posts/how-to-control-yeelight-and-your-smarthome-with-yeti

## Plugin Settings
* State Update Delay: The Time It Takes For States To Update.
* Discover Devices Delay: The Time It Takes To Discover New Devices.
* Enable Disconnected Devices: If Your Devices Have A Low Connection This Would Keep Them Connected At All Time("On" or "Off").
* Enable Log: If You Want To Troubleshoot This Would Create A Log("On" or "Off") .
* Enable Auto Update: If You Want The Plugin To Search For A New Version Every Time It Starts("On" or "Off")


Any Donations are welcome at www.paypal.me/ElyOshri1 and maybe soon Killer_BOSS would also open one
