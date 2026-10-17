"""Sensors populated by the airOS HTTP status endpoint."""
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfDataRate, UnitOfInformation, UnitOfTime
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

# Key -> (friendly name, unit, device class, state class).
# Include fields actually returned by airOS 4.0.4's status.cgi. Optional fields
# are only created when the device really supplies them, avoiding permanently
# unavailable entities for values this firmware does not expose.
SENSORS = {
    "signal": ("Wireless Signal", "dBm", SensorDeviceClass.SIGNAL_STRENGTH, None),
    "noise": ("Wireless Noise", "dBm", None, None),
    "ccq": ("Wireless CCQ", PERCENTAGE, None, None),
    "snr": ("Wireless SNR", "dB", None, None),
    "wlanTxRate": ("Wireless Transmit Rate", UnitOfDataRate.MEGABITS_PER_SECOND, None, None),
    "wlanRxRate": ("Wireless Receive Rate", UnitOfDataRate.MEGABITS_PER_SECOND, None, None),
    "essid": ("Wireless Network Name", None, None, None),
    "frequency": ("Wireless Frequency", "MHz", None, None),
    "wlanMac": ("Wireless MAC Address", None, None, None),
    "mac": ("Device MAC Address", None, None, None),
    "ip_address": ("Device IP Address", None, None, None),
    "hostname": ("Hostname", None, None, None),
    "uptime_seconds": ("Uptime", UnitOfTime.SECONDS, SensorDeviceClass.DURATION, SensorStateClass.TOTAL_INCREASING),
    "apmac": ("Access Point MAC Address", None, None, None),
    "channel": ("Wireless Channel", None, None, None),
    "date_time": ("Radio Date and Time", None, None, None),
    "security": ("Wireless Security", None, None, None),
    "qos": ("Wireless QoS", None, None, None),
    "antenna": ("Antenna Polarization", None, None, None),
    "ack": ("ACK Distance", "km", None, None),
    "rstatus": ("Wireless Radio Status Code", None, None, None),
    "err_nwids": ("Wireless Invalid Network IDs", None, None, SensorStateClass.TOTAL_INCREASING),
    "err_crypts": ("Wireless Crypto Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "err_frags": ("Wireless Fragment Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "err_retries": ("Wireless Retries", None, None, SensorStateClass.TOTAL_INCREASING),
    "err_beacons": ("Wireless Beacon Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "err_misc": ("Wireless Other Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_state": ("LAN State", None, None, None),
    "lan_rxbytes": ("LAN Received Data", UnitOfInformation.BYTES, None, SensorStateClass.TOTAL_INCREASING),
    "lan_rxpackets": ("LAN Received Packets", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_rxerrors": ("LAN Receive Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_txbytes": ("LAN Transmitted Data", UnitOfInformation.BYTES, None, SensorStateClass.TOTAL_INCREASING),
    "lan_txpackets": ("LAN Transmitted Packets", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_txerrors": ("LAN Transmit Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "wlan_rxbytes": ("Wireless Received Data", UnitOfInformation.BYTES, None, SensorStateClass.TOTAL_INCREASING),
    "wlan_rxpackets": ("Wireless Received Packets", None, None, SensorStateClass.TOTAL_INCREASING),
    "wlan_rxerrors": ("Wireless Receive Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "wlan_txbytes": ("Wireless Transmitted Data", UnitOfInformation.BYTES, None, SensorStateClass.TOTAL_INCREASING),
    "wlan_txpackets": ("Wireless Transmitted Packets", None, None, SensorStateClass.TOTAL_INCREASING),
    "wlan_txerrors": ("Wireless Transmit Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "ppp_ip": ("PPP IP Address", None, None, None),
    "ppp_rxbytes": ("PPP Received Data", UnitOfInformation.BYTES, None, SensorStateClass.TOTAL_INCREASING),
    "ppp_rxpackets": ("PPP Received Packets", None, None, SensorStateClass.TOTAL_INCREASING),
    "ppp_rxerrors": ("PPP Receive Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "ppp_txbytes": ("PPP Transmitted Data", UnitOfInformation.BYTES, None, SensorStateClass.TOTAL_INCREASING),
    "ppp_txpackets": ("PPP Transmitted Packets", None, None, SensorStateClass.TOTAL_INCREASING),
    "ppp_txerrors": ("PPP Transmit Errors", None, None, SensorStateClass.TOTAL_INCREASING),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    entities = [
        AirOSSensor(coordinator, entry, key, *description)
        for key, description in SENSORS.items()
        if key in data and data[key] is not None
    ]
    async_add_entities(entities)


class AirOSSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, label, unit, device_class, state_class):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = label
        self._attr_unique_id = f"{entry.data['host']}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data["host"])},
            manufacturer="Ubiquiti",
            model="NanoStation5 / airOS 4.x",
            name=entry.data["name"],
            configuration_url=coordinator.host.rstrip("/"),
        )

    @property
    def native_value(self):
        value = (self.coordinator.data or {}).get(self.key)
        if value is None:
            return None
        if self.key in {
            "signal", "noise", "ccq", "snr", "wlanTxRate", "wlanRxRate",
            "frequency", "uptime_seconds", "channel", "ack", "rstatus",
            "err_nwids", "err_crypts", "err_frags", "err_retries",
            "err_beacons", "err_misc", "lan_rxbytes", "lan_rxpackets",
            "lan_rxerrors", "lan_txbytes", "lan_txpackets", "lan_txerrors",
            "wlan_rxbytes", "wlan_rxpackets", "wlan_rxerrors", "wlan_txbytes",
            "wlan_txpackets", "wlan_txerrors", "ppp_rxbytes", "ppp_rxpackets",
            "ppp_rxerrors", "ppp_txbytes", "ppp_txpackets", "ppp_txerrors",
        }:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        return str(value)[:255]
