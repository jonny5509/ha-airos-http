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

from .const import DOMAIN, device_identifier

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
    "channel": ("Wireless Channel", None, None, None),
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
    "lan_ip_address": ("LAN IP Address", None, None, None),
    "lan_mac_address": ("LAN MAC Address", None, None, None),
    "lan_plugged": ("LAN Link Status", None, None, None),
    "lan_state": ("LAN State", None, None, None),
    "lan_rxbytes": ("LAN Received Data", UnitOfInformation.BYTES, None, SensorStateClass.TOTAL_INCREASING),
    "lan_rx_bytes": ("LAN Received Data", UnitOfInformation.BYTES, None, SensorStateClass.TOTAL_INCREASING),
    "lan_rxpackets": ("LAN Received Packets", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_rx_packets": ("LAN Received Packets", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_rxerrors": ("LAN Receive Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_rx_errors": ("LAN Receive Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_txbytes": ("LAN Transmitted Data", UnitOfInformation.BYTES, None, SensorStateClass.TOTAL_INCREASING),
    "lan_tx_bytes": ("LAN Transmitted Data", UnitOfInformation.BYTES, None, SensorStateClass.TOTAL_INCREASING),
    "lan_txpackets": ("LAN Transmitted Packets", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_tx_packets": ("LAN Transmitted Packets", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_txerrors": ("LAN Transmit Errors", None, None, SensorStateClass.TOTAL_INCREASING),
    "lan_tx_errors": ("LAN Transmit Errors", None, None, SensorStateClass.TOTAL_INCREASING),
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
    "apmac": ("AP MAC", None, None, None), "cfg_crc": ("Config CRC", None, None, None),
    "device_model": ("Device Model", None, None, None), "distance": ("Distance", None, None, None),
    "ack_timeout": ("ACK Timeout", None, None, None), "latitude": ("Latitude", None, None, None),
    "longitude": ("Longitude", None, None, None), "radio_date_time": ("Radio Date and Time", None, None, None),
    "deviceId": ("Device ID", None, None, None), "firmwareVersion": ("Firmware Version", None, None, None),
    "platform": ("Platform", None, None, None), "deviceIp": ("Configured Device IP Address", None, None, None),
}


def _friendly_name(key):
    """Create a readable label for unrecognised scalar fields."""
    overrides = {
        "wip": "Wireless IP Address",
        "wlan_ip_address": "Wireless IP Address",
        "wmac": "Wireless MAC Address",
        "lmac": "LAN MAC Address",
        "lip": "LAN IP Address",
        "plugged": "LAN Link Status",
        "rx bytes": "LAN Received Data",
        "rx errors": "LAN Receive Errors",
        "rx packets": "LAN Received Packets",
        "tx bytes": "LAN Transmitted Data",
        "tx errors": "LAN Transmit Errors",
        "tx packets": "LAN Transmitted Packets",
        "ap_mac": "AP MAC",
        "apmacaddr": "AP MAC",
        "wlan_apmac": "AP MAC",
        "cfgcrc": "Cfg CRC",
        "configcrc": "Cfg CRC",
        "config_crc": "Cfg CRC",
        "devicemodel": "Device Model",
        "model": "Device Model",
        "linkdistance": "Distance",
        "dist": "Distance",
        "lat": "Latitude",
        "lon": "Longitude",
        "lng": "Longitude",
    }
    return overrides.get(key.strip().lower(), key.replace("_", " ").replace("-", " ").strip().title())


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    entities = []

    # Ensure the parent radio device exists before creating interface devices.
    device_registry = dr.async_get(hass)
    parent_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_identifier(entry.data["host"]))},
        manufacturer="Ubiquiti",
        model=(data.get("device_model") or "Original airOS 3.x–4.x"),
        name=entry.data["name"],
        configuration_url=coordinator.host.rstrip("/"),
    )

    # Re-home legacy ETH0/ETH1/SWITCH0 devices under one LAN child, matching
    # the SSH integration while preserving existing entity IDs and history.
    host = entry.data["host"]
    lan_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{device_identifier(host)}_lan")},
        manufacturer="Ubiquiti",
        model="Original airOS 3.x–4.x LAN",
        name=f"{entry.data['name']} LAN",
        configuration_url=coordinator.host.rstrip("/"),
        via_device_id=parent_device.id,
    )
    # The initial HTTP response may not expose hardware identity. Update the
    # Home Assistant device once a later poll discovers the model.
    def _update_registered_device_model():
        detected_model = (coordinator.data or {}).get("device_model")
        current_device = device_registry.async_get_device_by_identifier(
            (DOMAIN, device_identifier(entry.data["host"])), entry.entry_id
        )
        if current_device and detected_model and current_device.model != detected_model:
            device_registry.async_update_device(current_device.id, model=detected_model)

    entry.async_on_unload(coordinator.async_add_listener(_update_registered_device_model))
    entity_registry = er.async_get(hass)
    interface_prefix = f"{entry.data['name']} Interface "
    for old_device in device_registry.async_get_devices(config_entry_id=entry.entry_id):
        if old_device.id in {lan_device.id, parent_device.id}:
            continue
        if old_device.config_entry_id != entry.entry_id:
            continue
        if not (old_device.name or "").startswith(interface_prefix):
            continue
        for registered_entity in list(entity_registry.entities.values()):
            if registered_entity.device_id == old_device.id:
                entity_registry.async_update_entity(registered_entity.entity_id, device_id=lan_device.id)
        if not any(e.device_id == old_device.id for e in entity_registry.entities.values()):
            device_registry.async_remove_device(old_device.id)

    # Prefer one canonical entity when old firmware reports the same counter
    # under both underscored and compact aliases. Keep the existing unique IDs
    # of the preferred entities so history and automations remain intact.
    sensor_aliases = {
        "lan_rx_bytes": "lan_rxbytes",
        "lan_rx_packets": "lan_rxpackets",
        "lan_rx_errors": "lan_rxerrors",
        "lan_tx_bytes": "lan_txbytes",
        "lan_tx_packets": "lan_txpackets",
        "lan_tx_errors": "lan_txerrors",
        "ppp_rx_bytes": "ppp_rxbytes",
        "ppp_rx_packets": "ppp_rxpackets",
        "ppp_rx_errors": "ppp_rxerrors",
        "ppp_tx_bytes": "ppp_txbytes",
        "ppp_tx_packets": "ppp_txpackets",
        "ppp_tx_errors": "ppp_txerrors",
        "wlan_rx_bytes": "wlan_rxbytes",
        "wlan_rx_packets": "wlan_rxpackets",
        "wlan_rx_errors": "wlan_rxerrors",
        "wlan_tx_bytes": "wlan_txbytes",
        "wlan_tx_packets": "wlan_txpackets",
        "wlan_tx_errors": "wlan_txerrors",
    }
    for key, description in SENSORS.items():
        canonical_key = sensor_aliases.get(key)
        if canonical_key and data.get(canonical_key) not in (None, ""):
            continue
        if key in data and data[key] is not None:
            entities.append(AirOSSensor(coordinator, entry, key, parent_device.id, *description))

    # Also expose every additional scalar field found in the HTTP responses.
    # This deliberately makes discovery broad so users can decide which raw
    # firmware-specific sensors they want to keep or disable later.
    duplicate_aliases = {
        # Some legacy HTTP payloads expose the same interface values under
        # short aliases and descriptive keys. Prefer the descriptive sensors.
        "lip": "lan_ip_address", "lmac": "lan_mac_address",
        "wmac": "wlanMac", "wip": "wip",
        "side_devicename": "hostname", "devicename": "hostname",
        "date_time": "radio_date_time", "datetime": "radio_date_time",
        "radio_datetime": "radio_date_time",
        "ap_mac": "apmac", "apmacaddr": "apmac", "wlan_apmac": "apmac",
        "cfgcrc": "cfg_crc", "configcrc": "cfg_crc", "config_crc": "cfg_crc",
        "devicemodel": "device_model", "model": "device_model",
        "linkdistance": "distance", "dist": "distance",
        "lat": "latitude", "lon": "longitude", "lng": "longitude",
        "lanip": "lan_ip_address", "lanmac": "lan_mac_address",
        "wirelessmac": "wlanMac", "wlan_mac": "wlanMac",
        "ppp_rx_bytes": "ppp_rxbytes", "ppp_rx_packets": "ppp_rxpackets",
        "ppp_rx_errors": "ppp_rxerrors", "ppp_tx_bytes": "ppp_txbytes",
        "ppp_tx_packets": "ppp_txpackets", "ppp_tx_errors": "ppp_txerrors",
    }
    for key, value in data.items():
        canonical_key = duplicate_aliases.get(key.lower())
        if canonical_key and data.get(canonical_key) not in (None, ""):
            continue
        if key in SENSORS or value is None or isinstance(value, (dict, list, tuple, set)):
            continue
        entities.append(
            AirOSSensor(
                coordinator, entry, key, parent_device.id, _friendly_name(key), None, None, None
            )
        )

    async_add_entities(entities)


class AirOSSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, parent_device_id, label, unit, device_class, state_class):
        super().__init__(coordinator)
        self.key = key
        self._attr_icon = {
            "signal": "mdi:signal",
            "noise": "mdi:waveform",
            "ccq": "mdi:chart-line",
            "snr": "mdi:signal",
            "wlanTxRate": "mdi:upload",
            "wlanRxRate": "mdi:download",
            "frequency": "mdi:sine-wave",
            "essid": "mdi:wifi",
            "wlanMac": "mdi:network-outline",
            "mac": "mdi:lan",
            "hostname": "mdi:form-textbox",
            "ip_address": "mdi:ip-network",
            "uptime_seconds": "mdi:timer-outline",
            "cpu_usage": "mdi:cpu-64-bit",
            "ram_usage_percent": "mdi:memory",
            "firmware_upgrade": "mdi:chip",
            "ethernet_rx_bytes": "mdi:download-network",
            "ethernet_tx_bytes": "mdi:upload-network",
            "wireless_rx_bytes": "mdi:download-network",
            "wireless_tx_bytes": "mdi:upload-network",
            "lan_rxbytes": "mdi:download-network",
            "lan_txbytes": "mdi:upload-network",
            "wlan_rxbytes": "mdi:download-network",
            "wlan_txbytes": "mdi:upload-network",
            "ppp_rxbytes": "mdi:download-network",
            "ppp_txbytes": "mdi:upload-network",
            "device_model": "mdi:router-wireless",
            "deviceId": "mdi:identifier",
            "firmwareVersion": "mdi:package-variant",
            "distance": "mdi:map-marker-distance",
            "latitude": "mdi:latitude",
            "longitude": "mdi:longitude",
            "radio_date_time": "mdi:clock-outline",
        }.get(key)
        self._attr_name = label
        self._attr_unique_id = f"{entry.data['host']}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        host = entry.data["host"]
        self._host = host
        main_device_keys = {
            "signal","noise","wlanTxRate","wlanRxRate","frequency","apmac","cfg_crc",
            "device_model","distance","ack_timeout","latitude","longitude","radio_date_time",
            "ppp_ip","ppp_rxbytes","ppp_rxpackets","ppp_rxerrors","ppp_txbytes","ppp_txpackets",
            "ppp_txerrors","deviceId","firmwareVersion","platform","deviceIp","mac","hostname",
            "uptime_seconds","cpu_model","cpu_usage","ram_usage_percent",
        }
        wireless_keys = {
            "ccq", "snr", "essid", "wlanMac", "channel", "security", "qos", "antenna",
            "ack", "rstatus", "err_nwids", "err_crypts", "err_frags", "err_retries",
            "err_beacons", "err_misc", "wlan_rxbytes", "wlan_rxpackets", "wlan_rxerrors",
            "wlan_txbytes", "wlan_txpackets", "wlan_txerrors",
        }
        if key in main_device_keys:
            device_name = entry.data["name"]
            identifiers = {(DOMAIN, device_identifier(host))}
            via_device = False
        elif key in wireless_keys or key in {"wmac", "wip"} or key.lower().startswith(("wlan_", "wireless_")):
            device_id = f"{device_identifier(host)}_wireless"
            device_name = f"{entry.data['name']} Wireless"
            identifiers = {(DOMAIN, device_id)}
            via_device = True
        elif key in {"lmac", "lip", "lan_state"} or key.lower().startswith("lan_"):
            # LAN interface sensors belong to their own child device under the radio.
            device_id = f"{device_identifier(host)}_lan"
            device_name = f"{entry.data['name']} LAN"
            identifiers = {(DOMAIN, device_id)}
            via_device = True
        elif key in {"wlanMac", "wlan_ip_address"}:
            # wmac and wip are wireless-interface identifiers.
            device_id = f"{host}_wireless"
            device_name = f"{entry.data['name']} Wireless"
            identifiers = {(DOMAIN, device_id)}
            via_device = True
        else:
            device_name = entry.data["name"]
            identifiers = {(DOMAIN, host)}
            via_device = False

        via_device_id = parent_device_id if via_device else None
        self._target_device_identifiers = identifiers
        self._target_via_device_id = via_device_id
        self._target_device_name = device_name
        self._entry_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers=identifiers,
            via_device_id=via_device_id,
            manufacturer="Ubiquiti",
            model=((coordinator.data or {}).get("device_model") or "Original airOS 3.x–4.x") if not via_device else (((coordinator.data or {}).get("device_model") or "Original airOS 3.x–4.x") + (" LAN" if key in {"lmac", "lip", "lan_state"} or key.lower().startswith("lan_") else " Wireless")),
            name=device_name,
            configuration_url=coordinator.host.rstrip("/"),
        )

    async def async_added_to_hass(self):
        """Ensure child devices exist and migrate entities from the legacy Ethernet device."""
        await super().async_added_to_hass()

        device_registry = dr.async_get(self.hass)
        entity_registry = er.async_get(self.hass)
        host = self._host
        is_lan_sensor = (
            self.key in {"lmac", "lip", "lan_state"}
            or self.key.lower().startswith("lan_")
        )

        if self._target_via_device_id is None:
            return

        device = device_registry.async_get_or_create(
            config_entry_id=self._entry_id,
            identifiers=self._target_device_identifiers,
            manufacturer="Ubiquiti",
            model=((self.coordinator.data or {}).get("device_model") or "Original airOS 3.x–4.x") + (" LAN" if is_lan_sensor else " Wireless"),
            name=self._target_device_name,
            configuration_url=self.coordinator.host.rstrip("/"),
            via_device=(DOMAIN, device_identifier(host)),
        )
        entity_entry = entity_registry.async_get(self.entity_id)
        if entity_entry is not None and entity_entry.device_id != device.id:
            entity_registry.async_update_entity(self.entity_id, device_id=device.id)

        if not is_lan_sensor:
            return

        # Existing LAN entities may still be assigned to the old Ethernet child.
        # Move them to the new LAN child, then remove the obsolete device if empty.
        legacy_device = device_registry.async_get_device_by_identifier(
            (DOMAIN, f"{device_identifier(host)}_ethernet"), self._entry_id
        )
        if legacy_device is None:
            return

        for registered_entity in list(entity_registry.entities.values()):
            if registered_entity.device_id == legacy_device.id:
                entity_registry.async_update_entity(
                    registered_entity.entity_id, device_id=device.id
                )

        if not any(
            registered_entity.device_id == legacy_device.id
            for registered_entity in entity_registry.entities.values()
        ):
            device_registry.async_remove_device(legacy_device.id)

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
            "err_beacons", "err_misc", "lan_rxbytes", "lan_rx_bytes",
            "lan_rxpackets", "lan_rx_packets", "lan_rxerrors", "lan_rx_errors",
            "lan_txbytes", "lan_tx_bytes", "lan_txpackets", "lan_tx_packets",
            "lan_txerrors", "lan_tx_errors", "lan_plugged",
            "wlan_rxbytes", "wlan_rxpackets", "wlan_rxerrors", "wlan_txbytes",
            "wlan_txpackets", "wlan_txerrors", "ppp_rxbytes", "ppp_rxpackets",
            "ppp_rxerrors", "ppp_txbytes", "ppp_txpackets", "ppp_txerrors",
        }:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        return str(value)[:255]
