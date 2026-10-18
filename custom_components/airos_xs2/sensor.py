"""Home Assistant sensors for legacy Ubiquiti AirOS over HTTP."""
import re

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


# Keys produced by the HTTP coordinator are deliberately stable: they are also
# used to build entity unique IDs, so changing them would reset entity history.
BASE_SENSORS = {
    "signal": ("Wireless Signal", "dBm"),
    "noise": ("Wireless Noise", "dBm"),
    "ccq": ("Wireless CCQ", "%"),
    "snr": ("Wireless SNR", "dB"),
    "wlanTxRate": ("Wireless Transmit Rate", "Mbit/s"),
    "wlanRxRate": ("Wireless Receive Rate", "Mbit/s"),
}

OPTIONAL_SENSORS = {
    "essid": ("Wireless Network Name (SSID)", None),
    "frequency": ("Wireless Frequency", "MHz"),
    "wlanMac": ("Wireless MAC Address", None),
    "wireless_mac": ("Wireless MAC Address", None),
    "ethernet_mac": ("Ethernet MAC Address", None),
    "ethernet_interface_state": ("Ethernet Interface State", None),
    "wireless_interface_state": ("Wireless Interface State", None),
    "mac": ("Device MAC Address", None),
    "mode": ("Wireless Mode", None),
    "hostname": ("Hostname", None),
    "uptime_seconds": ("Uptime", "s"),
    "ip_address": ("Device IP Address", None),
    "cpu_model": ("CPU Model", None),
    "cpu_usage": ("CPU Usage", "%"),
    "firmware_upgrade": ("Firmware Upgrade", None),
    "ram_usage_percent": ("RAM Usage", "%"),
    "ethernet_rx_bytes": ("Ethernet Bytes Received", "B"),
    "ethernet_tx_bytes": ("Ethernet Bytes Sent", "B"),
    "wireless_rx_bytes": ("Wireless Bytes Received", "B"),
    "wireless_tx_bytes": ("Wireless Bytes Sent", "B"),
}

DEVICE_METADATA = {
    "deviceId": ("Device ID", None),
    "firmwareVersion": ("Firmware Version", None),
    "platform": ("Platform", None),
    "deviceIp": ("Configured Device IP Address", None),
}

# Preserve familiar entity names for keys commonly emitted by AirOS firmware.
_NAME_OVERRIDES = {
    **{key: value[0] for key, value in BASE_SENSORS.items()},
    **{key: value[0] for key, value in OPTIONAL_SENSORS.items()},
    **{key: value[0] for key, value in DEVICE_METADATA.items()},
}


def _parse_device_name(raw_name):
    """Return a clean device name and recognised comma-separated metadata."""
    parts = [part.strip() for part in str(raw_name).split(",")]
    known_keys = {key.lower(): key for key in DEVICE_METADATA}
    metadata = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        canonical_key = known_keys.get(key.strip().lower())
        if canonical_key and value.strip():
            metadata[canonical_key] = value.strip()
    return parts[0] or "AirOS Device", metadata


def _friendly_name(key):
    """Turn arbitrary flattened status keys into readable sensor names."""
    if key in _NAME_OVERRIDES:
        return _NAME_OVERRIDES[key]
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(key))
    words = re.sub(r"[_-]+", " ", name).split()
    acronyms = {
        "ccq": "CCQ", "cpu": "CPU", "dbm": "dBm", "eth": "Ethernet",
        "id": "ID", "ip": "IP", "lan": "Ethernet", "mac": "MAC",
        "mhz": "MHz", "ram": "RAM", "rx": "RX", "snr": "SNR",
        "ssid": "SSID", "tx": "TX", "wifi": "Wi-Fi", "wlan": "Wireless",
    }
    return " ".join(acronyms.get(word.lower(), word.capitalize()) for word in words) or "Unknown"


def _device_kind(key):
    """Map a sensor to the main radio, Wireless, or Ethernet device."""
    lowered = str(key).lower()
    if lowered.startswith(("wlan", "wireless_")) or key in BASE_SENSORS or key in {
        "essid", "frequency", "wireless_mac", "wireless_interface_state", "mode",
    }:
        return "wireless"
    if lowered.startswith(("ethernet_", "lan", "eth")) or key == "ethernet_mac":
        return "ethernet"
    return "main"


def _numeric(value):
    """Return numeric values as floats, leaving text sensors untouched."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    try:
        text = str(value).strip()
        if not text:
            return value
        return float(text)
    except (TypeError, ValueError):
        return value


async def async_setup_entry(hass, entry, async_add_entities):
    """Create the sensor entities and maintain device/entity registry layout."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    display_name, metadata = _parse_device_name(entry.data.get("name", "AirOS Device"))
    host = entry.data["host"]

    device_registry = dr.async_get(hass)
    parent = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, host)},
        name=display_name,
        manufacturer="Ubiquiti",
        model=data.get("device_model") or "Ubiquiti AirOS",
    )
    ethernet = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{host}_ethernet")},
        name=f"{display_name} Ethernet",
        manufacturer="Ubiquiti",
        model=f"{data.get('device_model') or 'AirOS'} Ethernet",
        via_device=(DOMAIN, host),
    )
    wireless = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{host}_wireless")},
        name=f"{display_name} Wireless",
        manufacturer="Ubiquiti",
        model=f"{data.get('device_model') or 'AirOS'} Wireless",
        via_device=(DOMAIN, host),
    )

    entity_registry = er.async_get(hass)
    # Older releases exposed these raw memory values as entities. They now
    # belong as attributes on RAM Usage, so remove only those obsolete entities.
    obsolete_memory_keys = {"mem_total_bytes", "mem_free_bytes", "mem_available_bytes"}
    prefix = f"{host}_"
    for entity in list(entity_registry.entities.values()):
        if entity.config_entry_id != entry.entry_id or not entity.unique_id.startswith(prefix):
            continue
        key = entity.unique_id[len(prefix):]
        if key in obsolete_memory_keys:
            entity_registry.async_remove(entity.entity_id)
            continue
        kind = _device_kind(key)
        desired_device = {
            "main": parent.id,
            "wireless": wireless.id,
            "ethernet": ethernet.id,
        }[kind]
        if entity.device_id != desired_device:
            entity_registry.async_update_entity(entity.entity_id, device_id=desired_device)

    def update_device_model():
        model = (coordinator.data or {}).get("device_model")
        if not model:
            return
        device_models = (
            ({(DOMAIN, host)}, model),
            ({(DOMAIN, f"{host}_wireless")}, f"{model} Wireless"),
            ({(DOMAIN, f"{host}_ethernet")}, f"{model} Ethernet"),
        )
        for identifiers, wanted in device_models:
            device = device_registry.async_get_device(identifiers=identifiers)
            if device and device.model != wanted:
                device_registry.async_update_device(device.id, model=wanted)

    entry.async_on_unload(coordinator.async_add_listener(update_device_model))

    entities = []
    registered_keys = set()

    def add_sensor(key, label, unit=None, *, static_value=None):
        if key in registered_keys:
            return
        entities.append(
            AirOSSensor(
                coordinator=coordinator,
                entry=entry,
                key=key,
                label=label,
                unit=unit,
                display_name=display_name,
                static_value=static_value,
                device_kind=_device_kind(key) if static_value is None else "main",
                parent_device_id=parent.id,
            )
        )
        registered_keys.add(key)

    for key, (label, unit) in BASE_SENSORS.items():
        add_sensor(key, label, unit)

    # Register known optional entities even before the first HTTP response
    # contains their fields, allowing later polls to make them available.
    always_register = {
        "ip_address", "uptime_seconds", "ethernet_interface_state",
        "wireless_interface_state", "cpu_usage", "firmware_upgrade",
        "ram_usage_percent",
    }
    for key, (label, unit) in OPTIONAL_SENSORS.items():
        value = data.get(key)
        if key in always_register or value not in (None, ""):
            # Avoid two entities for the same wireless MAC when AirOS provides
            # both the native wlanMac field and the interface-probe alias.
            if key == "wireless_mac" and data.get("wlanMac") not in (None, ""):
                continue
            add_sensor(key, label, unit)

    # The firmware detail values and memory counters are attributes of their
    # summary entities, not standalone entities.
    consumed = set(registered_keys)
    consumed.update(key for key in data if key.startswith("firmware_upgrade_"))
    consumed.update({"mem_total_bytes", "mem_free_bytes", "mem_available_bytes"})

    for key, value in data.items():
        if key not in consumed and value not in (None, ""):
            add_sensor(key, _friendly_name(key))

    for key, value in metadata.items():
        label, unit = DEVICE_METADATA[key]
        add_sensor(f"device_metadata_{key}", label, unit, static_value=value)

    async_add_entities(entities)


class AirOSSensor(SensorEntity):
    """A sensor backed by a field in the coordinator's HTTP status data."""

    def __init__(
        self, coordinator, entry, key, label, unit=None, display_name=None,
        static_value=None, device_kind="main", parent_device_id=None,
    ):
        self.coordinator = coordinator
        self._entry = entry
        self.key = key
        self._static_value = static_value
        self._device_kind = device_kind
        self._parent_device_id = parent_device_id
        self._display_name = display_name or entry.data.get("name", "AirOS Device")
        self._attr_name = label
        self._attr_unique_id = f"{entry.data['host']}_{key}"
        if unit:
            self._attr_native_unit_of_measurement = unit

        if key in {"signal", "noise"}:
            self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        elif key == "frequency":
            self._attr_device_class = SensorDeviceClass.FREQUENCY
        elif key == "uptime_seconds":
            self._attr_device_class = SensorDeviceClass.DURATION
        elif key in {
            "ethernet_rx_bytes", "ethernet_tx_bytes",
            "wireless_rx_bytes", "wireless_tx_bytes",
        }:
            self._attr_device_class = SensorDeviceClass.DATA_SIZE
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif key in {
            "signal", "noise", "ccq", "snr", "wlanTxRate", "wlanRxRate",
            "cpu_usage", "ram_usage_percent",
        }:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key == "frequency":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        host = self._entry.data["host"]
        if self._device_kind == "wireless":
            identifier = f"{host}_wireless"
            device_name = f"{self._display_name} Wireless"
            model_suffix = "Wireless"
        elif self._device_kind == "ethernet":
            identifier = f"{host}_ethernet"
            device_name = f"{self._display_name} Ethernet"
            model_suffix = "Ethernet"
        else:
            identifier = host
            device_name = self._display_name
            model_suffix = ""

        model = (self.coordinator.data or {}).get("device_model") or "Ubiquiti AirOS"
        if model_suffix:
            model = f"{model} {model_suffix}"
        info = {
            "identifiers": {(DOMAIN, identifier)},
            "name": device_name,
            "manufacturer": "Ubiquiti",
            "model": model,
        }
        if self._device_kind != "main":
            info["via_device"] = (DOMAIN, host)
        return DeviceInfo(**info)

    @property
    def native_value(self):
        if self._static_value is not None:
            return self._static_value
        value = (self.coordinator.data or {}).get(self.key)
        if self.key in {
            "signal", "noise", "ccq", "snr", "wlanTxRate", "wlanRxRate",
            "frequency", "uptime_seconds", "cpu_usage", "ram_usage_percent",
            "ethernet_rx_bytes", "ethernet_tx_bytes",
            "wireless_rx_bytes", "wireless_tx_bytes",
        }:
            return _numeric(value)
        return value

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        if self.key == "ram_usage_percent":
            return {
                key: data[key]
                for key in ("mem_total_bytes", "mem_free_bytes", "mem_available_bytes")
                if data.get(key) is not None
            } or None
        if self.key == "firmware_upgrade":
            return {
                key.removeprefix("firmware_upgrade_"): data[key]
                for key in (
                    "firmware_upgrade_installed_version",
                    "firmware_upgrade_latest_version",
                    "firmware_upgrade_reason",
                    "firmware_upgrade_source",
                )
                if data.get(key) is not None
            } or None
        return None
