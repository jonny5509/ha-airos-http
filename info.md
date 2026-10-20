# Ubiquiti AirOS (HTTP)

Home Assistant custom integration for monitoring legacy Ubiquiti airOS 4.x radios through the device's local web interface.

- **Domain:** `airos_xs2`
- **Current integration version:** `2.1.7`
- **Target firmware used for comparison:** `XS5.ar2313.v4.0.4.5074.150724.1344`
- **Communication:** Local HTTP polling; credentials and status traffic are not encrypted
- **Documentation:** https://github.com/jonny5509/ha-airos-http
- **Issues:** https://github.com/jonny5509/ha-airos-http/issues
- **Related SSH integration:** https://github.com/jonny5509/ha-airos-ssh

Compatibility and sensor availability depend on the radio model, firmware, and fields returned by its HTTP status interface. The HTTP edition may expose fewer diagnostic values than the SSH edition.

**Security:** Use only on a trusted LAN or VPN. Do not expose the radio's management interface to the public internet, and do not reuse sensitive credentials on an untrusted network.

This integration is community-maintained and is not affiliated with Ubiquiti.