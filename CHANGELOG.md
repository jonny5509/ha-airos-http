# Changelog

This changelog records verified changes from the repository history. Older entries are retained below; entries before 2.1.1 may not be complete.

## 2.1.7

- Align the main radio device's diagnostic sensors with the SSH integration where the HTTP response provides those values.
- Remove duplicate sensor aliases so equivalent fields do not create duplicate entities.
- Improve device naming by using the radio's configured hostname when the integration entry still has a generic default name.
- Update project documentation and compatibility/security guidance.

## 2.1.6

- Continue aligning HTTP sensor coverage and device diagnostics with the shared AirOS sensor list.

## 2.1.5

- Repository history does not provide a sufficiently clear release summary for this version.

## 2.1.4

- Repository history does not provide a sufficiently clear release summary for this version.

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

## Notes

- Sensor availability depends on the device model, firmware, and fields returned by the radio.
- The HTTP interface uses plain HTTP; credentials and status data are not encrypted.
- Changes to older versions are only listed where supported by the available repository history.
