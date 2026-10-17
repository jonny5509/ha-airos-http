# Ubiquiti AirOS over HTTP (legacy XS5 / airOS 4.0.4)

Home Assistant custom integration that polls the legacy airOS web interface over HTTP instead of SSH.

**Target firmware:** `XS5.ar2313.v4.0.4.5074.150724.1344` (NanoStation5 / legacy airOS 4.x).

## Installation

1. Copy `custom_components/airos_xs2` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Add the **Ubiquiti AirOS (HTTP)** integration from Settings → Devices & services.
4. Enter the device name, the full URL (for example `http://192.168.1.20`), and the device's web-interface username and password.

## How it works

The integration uses the legacy `/login.cgi` form login and session cookies, then reads `/status.cgi`. This is intended for older airOS firmware; it does not use SSH or run shell commands on the radio. The exact status fields depend on the device's HTTP response, so only fields actually present in `status.cgi` can be populated. CPU, memory, and interface byte counters formerly collected from procfs are not guaranteed to be exposed by the HTTP endpoint.

## Troubleshooting

- Make sure the radio's HTTP web interface is reachable from Home Assistant.
- Test the device's login in a browser first.
- If sensors remain unavailable, inspect the response body from `http://DEVICE-IP/status.cgi` after logging in. If it is HTML rather than JSON, this build's status endpoint differs from the expected legacy response; share a redacted sample so the parser can be adapted.
- Do not expose the radio's management interface directly to the public internet. Use a trusted LAN or VPN.

## Firmware

The code includes a legacy firmware comparison for NanoStation5 and recognizes `4.0.4.5074` as the published final release. Verify the hardware model before applying firmware to any device.
