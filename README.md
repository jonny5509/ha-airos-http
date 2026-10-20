# Ubiquiti AirOS over HTTP (legacy XS5 / airOS 4.0.4)

[![Downloads](https://img.shields.io/github/downloads/jonny5509/ha-airos-http/total?label=downloads)](https://github.com/jonny5509/ha-airos-http/releases)

**Current integration version:** `2.1.7` (see `custom_components/airos_xs2/manifest.json`)

**Canonical repository:** https://github.com/jonny5509/ha-airos-http  
**Git clone URL:** https://github.com/jonny5509/ha-airos-http.git

Home Assistant custom integration for legacy Ubiquiti AirOS devices. This variant communicates with the radio using **plain HTTP only**; it does not use SSH or HTTPS.

**Target firmware:** `XS5.ar2313.v4.0.4.5074.150724.1344` (legacy airOS 4.x).

## Features

- UI-based setup through Home Assistant Config Flow
- HTTP login using the legacy `/login.cgi` form and session cookies
- Polls `/status.cgi` and parses JSON or legacy JavaScript-style status assignments
- Wireless signal, noise, CCQ, SNR, TX/RX rate, SSID, frequency, and wireless MAC when reported by the radio
- Device identity and status sensors, including hostname, IP/MAC address, uptime, and other values returned by the firmware
- Optional LAN, wireless, and PPP interface counters and diagnostics when exposed by the device
- HACS-compatible Home Assistant integration

Sensors are created from values actually returned by the device. Available sensors therefore depend on the firmware and its HTTP status response.

## Installation

### HACS

1. In HACS, open the custom repositories menu.
2. Add `https://github.com/jonny5509/ha-airos-http` as an **Integration** repository.
3. Install **Ubiquiti AirOS (HTTP)** from that repository and restart Home Assistant.
4. Add the integration from **Settings → Devices & services → Add integration**.

Use the canonical `ha-airos-http` repository URL above, not the old `http-AirOS` repository URL. If HACS has the old custom repository saved, remove that entry and add the canonical URL again.

### Manual

1. Download this repository.
2. Copy `custom_components/airos_xs2` into your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.
4. Add **Ubiquiti AirOS (HTTP)** from **Settings → Devices & services → Add integration**.
5. Enter a device name, IP address (for example `192.168.1.20`), and the device's web-interface username and password. The integration normalizes the address to `http://`.

## How it works

The integration signs in through the legacy `/login.cgi` form, maintains the session cookies, and requests `/status.cgi` on its polling cycle. It supports JSON and common JavaScript assignment formats returned by older airOS firmware. SSH is not used and no shell commands are run on the radio.

The HTTP interface may not expose every value available through SSH. In particular, CPU usage, memory statistics, and some interface counters may be unavailable on this firmware.

## Troubleshooting

- Confirm the radio's HTTP web interface is reachable from Home Assistant.
- If sensors remain unavailable, inspect the response from `http://DEVICE-IP/status.cgi` after logging in. Legacy airOS versions may return JavaScript-style assignments rather than JSON.
- If you share a sample response to help improve parsing, remove passwords, cookies, tokens, and other secrets first.
- If HACS tries to download a URL under `/archive/refs/heads/<short-commit>.zip`, it may be treating a commit ID as a branch name. Remove the stale custom repository entry, add the canonical repository URL, and choose the `main` branch if prompted.
- Plain HTTP does not encrypt credentials or status data. Keep management access on a trusted LAN or VPN and do not expose it to the public internet.

## Firmware

The integration recognizes `4.0.4.5074` as the target NanoStation5 release for its firmware comparison. Verify the hardware model and firmware compatibility before applying firmware to any device.

## Related project

The separate SSH-based integration is available at https://github.com/jonny5509/ha-airos-ssh. The HTTP and SSH variants use different transports and may expose different sensors.
