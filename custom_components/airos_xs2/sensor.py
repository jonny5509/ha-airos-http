"""Sensors populated by the airOS HTTP status endpoint."""
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfDataRate, UnitOfInformation, UnitOfTime
from homeassistant.helpers import device_registry as dr, entity_registry as er
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
    "wip": ("Wireless IP Address", None, None, None),
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


def _friendly_name(key):
    """Create a readable label for unrecognised scalar fields."""
    return key.replace("_", " ").replace("-", " ").strip().title()


def _registered_model(coordinator, identifiers):
    """Return the detected model, with interface suffixes for child devices."""
    model = (coordinator.data or {}).get("device_model") or "Ubiquiti"
    if str(model).strip().lower() in {"ubnt", "ubiquiti", "unknown", "air os", "airos", "ubiquiti airos"}:
        model = "Ubiquiti"
    identifier_text = " ".join(str(value) for _, value in identifiers)
    if identifier_text.endswith("_ethernet"):
        return f"{model} Ethernet"
    if identifier_text.endswith("_wireless"):
        return f"{model} Wireless"
    return model


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    entities = []

    # Ensure the parent radio device exists before creating interface devices.
    device_registry = dr.async_get(hass)
    parent_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data["host"])},
        manufacturer="Ubiquiti",
        model=_registered_model(coordinator, {(DOMAIN, entry.data["host"])}),
        name=entry.data["name"],
        configuration_url=coordinator.host.rstrip("/"),
    )

    # Keep the parent registry model in sync if hardware identification appears
    # only after a later successful poll.
    def _update_registered_device_model():
        detected_model = (coordinator.data or {}).get("device_model")
        if not detected_model:
            return
        current_device = device_registry.async_get_device(
            identifiers={(DOMAIN, entry.data["host"])}
        )
        if current_device and current_device.model != detected_model:
            device_registry.async_update_device(current_device.id, model=detected_model)
        for suffix in ("_ethernet", "_wireless"):
            child = device_registry.async_get_device(
                identifiers={(DOMAIN, f"{entry.data['host']}{suffix}")}
            )
            child_model = f"{detected_model}{suffix.replace('_', ' ').title()}"
            if child and child.model != child_model:
                device_registry.async_update_device(child.id, model=child_model)

    entry.async_on_unload(coordinator.async_add_listener(_update_registered_device_model))

    # First add known sensors with units and device classes.
    for key, description in SENSORS.items():
        if key in data and data[key] is not None:
            entities.append(AirOSSensor(coordinator, entry, key, parent_device.id, *description))

    # Also expose every additional scalar field found in the HTTP responses.
    # This deliberately makes discovery broad so users can decide which raw
    # firmware-specific sensors they want to keep or disable later.
    for key, value in data.items():
        if key in SENSORS or value is None or isinstance(value, (dict, list, tuple, set)):
            continue
        entities.append(
            AirOSSensor(
                coordinator, entry, key, parent_device.id, _friendly_name(key), None, None, None
            )
        )

    async_add_entities(entities)


def _device_kind(key):
    """Return which Home Assistant device should own a sensor."""
    normalized = key.lower()

    # Check wireless first: "wlan" contains "lan".
    if (
        normalized.startswith(("wlan", "wireless_"))
        or key in {
            "signal", "noise", "ccq", "snr", "essid", "frequency",
            "wlanTxRate", "wlanRxRate", "wlanMac", "wip", "apmac",
            "channel", "security", "qos", "antenna", "ack", "rstatus",
            "err_nwids", "err_crypts", "err_frags", "err_retries",
            "err_beacons", "err_misc",
        }
    ):
        return "wireless"

    # Device-wide MAC/IP and uptime remain on the main radio device.
    if key in {"mac", "ip_address", "hostname", "uptime_seconds", "date_time"}:
        return "main"

    if (
        normalized.startswith(("lan_", "ethernet_", "eth"))
        or key in {"lmac", "lip", "lan_state"}
    ):
        return "ethernet"

    return "main"


class AirOSSensor(CoordinatorEntity, SensorEntity):
    # Match the SSH integration: include the configured device name in the entity name.
    _attr_has_entity_name = False

    def __init__(self, coordinator, entry, key, parent_device_id, label, unit, device_class, state_class):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = f"{entry.data['name']} {label}"
        self._attr_unique_id = f"{entry.data['host']}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

        host = entry.data["host"]
        self._entry_id = entry.entry_id
        self._parent_device_id = parent_device_id
        self._device_kind = _device_kind(key)

        if self._device_kind == "ethernet":
            self._device_identifiers = {(DOMAIN, f"{host}_ethernet")}
            self._device_name = f"{entry.data['name']} Ethernet"
            self._via_device_id = parent_device_id
        elif self._device_kind == "wireless":
            self._device_identifiers = {(DOMAIN, f"{host}_wireless")}
            self._device_name = f"{entry.data['name']} Wireless"
            self._via_device_id = parent_device_id
        else:
            self._device_identifiers = {(DOMAIN, host)}
            self._device_name = entry.data["name"]
            self._via_device_id = None

        self._attr_device_info = DeviceInfo(
            identifiers=self._device_identifiers,
            via_device_id=self._via_device_id,
            manufacturer="Ubiquiti",
            model=_registered_model(coordinator, self._device_identifiers),
            name=self._device_name,
            configuration_url=coordinator.host.rstrip("/"),
        )

    async def async_added_to_hass(self):
        """Create child devices and migrate existing entities to their proper device."""
        await super().async_added_to_hass()
        if self._device_kind == "main":
            return

        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_or_create(
            config_entry_id=self._entry_id,
            identifiers=self._device_identifiers,
            manufacturer="Ubiquiti",
            model=_registered_model(self.coordinator, self._device_identifiers),
            name=self._device_name,
            configuration_url=self.coordinator.host.rstrip("/"),
            via_device_id=self._parent_device_id,
        )
        entity_registry = er.async_get(self.hass)
        entity_entry = entity_registry.async_get(self.entity_id)
        if entity_entry is not None and entity_entry.device_id != device.id:
            entity_registry.async_update_entity(self.entity_id, device_id=device.id)

    @property
    def native_value(self):
        value = (self.coordinator.data or {}).get(self.key)
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
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
