"""Sensors populated by the airOS HTTP status endpoint."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SENSORS = {
    "signal": ("Wireless Signal", "dBm"),
    "noise": ("Wireless Noise", "dBm"),
    "ccq": ("Wireless CCQ", "%"),
    "snr": ("Wireless SNR", "dB"),
    "wlanTxRate": ("Wireless Transmit Rate", "Mbit/s"),
    "wlanRxRate": ("Wireless Receive Rate", "Mbit/s"),
    "essid": ("Wireless Network Name", None),
    "frequency": ("Wireless Frequency", "MHz"),
    "wlanMac": ("Wireless MAC Address", None),
    "mac": ("Device MAC Address", None),
    "hostname": ("Hostname", None),
    "ip_address": ("Device IP Address", None),
    "firmwareVersion": ("Firmware Version", None),
    "platform": ("Platform", None),
    "uptime_seconds": ("Uptime", "s"),
    "firmware_upgrade": ("Firmware Upgrade", None),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        AirOSSensor(coordinator, entry, key, label, unit)
        for key, (label, unit) in SENSORS.items()
    ]
    async_add_entities(entities)


class AirOSSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, label, unit):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = label
        self._attr_unique_id = f"{entry.data['host']}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data["host"])},
            manufacturer="Ubiquiti",
            model="NanoStation5 / airOS 4.x",
            name=entry.data["name"],
            configuration_url=entry.data["host"],
        )

    @property
    def native_value(self):
        value = (self.coordinator.data or {}).get(self.key)
        if value is None:
            return None
        if self.key in {"signal", "noise", "ccq", "snr", "wlanTxRate", "wlanRxRate", "frequency", "uptime_seconds"}:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        return str(value)[:255]
