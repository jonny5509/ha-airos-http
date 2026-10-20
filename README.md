# Ubiquiti AirOS (SSH / HTTP)

Home Assistant custom integration for legacy Ubiquiti airOS devices. Select **SSH** or **HTTP** during setup.

## Features

- One integration and one setup flow for both connection methods.
- SSH backend retains the existing `mca-status` sensors, system probes, and reboot switch.
- HTTP backend retains the legacy `login.cgi` / `status.cgi` polling, discovered status sensors, and reboot button.
- Existing HTTP entries are identified by their saved `http://` host. Existing SSH entries without a protocol are treated as SSH for backward compatibility.

## Installation

### HACS

1. Add `https://github.com/jonny5509/ha-airos-http` as a custom repository in HACS.
2. Choose **Integration**, install it, and restart Home Assistant.
3. Add **Ubiquiti AirOS** from Settings → Devices & services.
4. Choose SSH or HTTP and enter the device details.

### Manual

Copy `custom_components/airos_xs2` into `/config/custom_components/`, restart Home Assistant, and add **Ubiquiti AirOS**.

## Connection methods

### SSH

Uses `asyncssh` and legacy SSH algorithms for older airOS firmware. SSH provides richer telemetry such as CPU, memory, uptime, interface counters, and additional `mca-status` fields. Enable SSH on the device.

### HTTP

Uses the legacy airOS web interface and plain HTTP. It does not require SSH, but can only expose values returned by the device's web endpoints. HTTP does not encrypt credentials or telemetry; use only on a trusted LAN or VPN and never expose the management interface directly to the public internet.

## Migration notes

The integration domain remains `airos_xs2`. Existing HTTP entries with a saved `http://` host continue to use HTTP. Existing SSH entries with a plain host and no saved protocol are treated as SSH. After updating, check each device's entities and confirm its selected connection method.

## Compatibility

Designed for legacy Ubiquiti airOS 4.x devices. Availability of sensors and commands depends on firmware and hardware.

## License

MIT
