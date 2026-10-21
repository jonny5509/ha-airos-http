# Changelog

This changelog summarizes verified changes from the repository history. Historical entries before 2.1.1 may be incomplete.

## 2.3.0

- Remove the `hub` integration-type classification so Home Assistant uses the standard integration entry wording.
- Fix duplicate HTTP interface sensors and continue deduplicating legacy sensor aliases.
- Clean up sensor entity names and icons for more consistent presentation.
- Align legacy device-model detection with the SSH integration, including additional identity-field variants.
- Normalize device identifiers to improve consistency across supported AirOS responses.

## 2.1.8

- Improve setup form wording and field descriptions for the device name, host, and HTTP web-interface credentials.
- Provide a clearer example HTTP address for the host field.

## 2.1.7

- Align the main radio device's diagnostic sensors with the SSH integration where the HTTP response provides those values.
- Remove duplicate sensor aliases so equivalent fields do not create duplicate entities.
- Improve device naming by using the radio's configured hostname when the integration entry still has a generic default name.
- Update project documentation and compatibility/security guidance.

## 2.1.6

- Continue aligning HTTP sensor coverage and device diagnostics with the shared AirOS sensor list.

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
- Older releases are omitted where the available repository history does not support a reliable summary.
