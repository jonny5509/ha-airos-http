# Changelog

## 2.1.3

- Give the LAN interface its own child device under the main radio device.
- Assign LAN IP/MAC, link state, and RX/TX traffic counters to the LAN child.
- Migrate entities from the legacy Ethernet child device to the LAN child.

## 2.1.2

- Use LAN terminology consistently; remove the remaining Ethernet wording.

## 2.1.1

- Add LAN IP address, LAN MAC address, and LAN plugged-state sensors.
- Add LAN RX/TX byte, packet, and error counters.
- Normalize additional airOS LAN field names from the HTTP status response.

Note: This release has not yet been validated against a live radio response.
