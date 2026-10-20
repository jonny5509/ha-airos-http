# Ubiquiti AirOS (HTTP)

[![Downloads](https://img.shields.io/github/downloads/jonny5509/ha-airos-http/total?label=downloads)](https://github.com/jonny5509/ha-airos-http/releases)

**Version:** 2.2.0  
**Transport:** HTTP  
**Repository:** https://github.com/jonny5509/ha-airos-http

A Home Assistant custom integration for monitoring the original Ubiquiti NanoStation 2 (NS2/XS2) and NanoStation 5 (NS5/XS5) running legacy airOS 3.x–4.x. This edition uses the radio's web interface over plain HTTP; it does not use SSH or HTTPS.

## Features

- Home Assistant UI setup
- Wireless signal, noise, CCQ, SNR, TX/RX rates, SSID, and frequency when reported by the device
- Device hostname, IP/MAC addresses, uptime, and other status information
- Optional LAN, wireless, and PPP interface counters
- Parses JSON and legacy JavaScript-style status responses

Available sensors depend on the radio model, firmware, and fields exposed by its HTTP status page.

## Compatibility

- Intended specifically for the original NanoStation 2 (NS2/XS2) and NanoStation 5 (NS5/XS5) with airOS 3.x–4.x.
- Other product families, including NanoStation Loco, Bullet, PicoStation, and PowerStation, are outside the supported scope.
- Target firmware used for comparison: `XS5.ar2313.v4.0.4.5074.150724.1344`.
- The integration logs in through `/login.cgi` and polls `/status.cgi`.
- Automated tests cover JSON status payloads and common JavaScript assignment formats, including alternate key spellings and NS2/NS5 identity aliases.
- Firmware-specific fields vary; parser-format tests do not mean every airOS 3.x/4.x build has been verified on physical hardware.

The HTTP interface may expose fewer diagnostics than the SSH edition, including limited CPU, memory, or interface-counter data.

## Installation

### HACS

1. Open **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/jonny5509/ha-airos-http` and select **Integration**.
3. Install **Ubiquiti AirOS (HTTP)** and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and select **Ubiquiti AirOS (HTTP)**.

Use this canonical repository URL if you previously added an older repository address.

### Manual

1. Download or clone this repository.
2. Copy `custom_components/airos_xs2` into your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.
4. Add **Ubiquiti AirOS (HTTP)** from **Settings → Devices & services → Add integration**.
5. Enter the radio's IP address and web-interface credentials.

The integration uses an `http://` address. Make sure Home Assistant can reach the radio's web interface.

## Troubleshooting

- Confirm the radio's HTTP interface is reachable from Home Assistant.
- If sensors are unavailable, check the logged-in `/status.cgi` response and whether it contains the expected fields.
- Legacy firmware may return JavaScript-style assignments rather than JSON.
- Remove passwords, cookies, tokens, and other secrets before sharing logs or responses.

## Security

Plain HTTP does not encrypt credentials or status data. Keep management access on a trusted LAN or VPN and do not expose the radio's management interface to the public internet.

## Related project

Prefer SSH-based polling and additional best-effort diagnostics? See the [Ubiquiti AirOS (SSH) integration](https://github.com/jonny5509/ha-airos-ssh).
