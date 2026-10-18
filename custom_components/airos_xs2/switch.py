"""Reboot switch for legacy airOS devices, using HTTP rather than SSH."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


def _display_name(raw_name):
    """Hide recognised discovery metadata from the device's display name."""
    if any(field in raw_name for field in ("deviceId=", "firmwareVersion=", "platform=", "deviceIp=")):
        return raw_name.split(",", 1)[0].strip() or raw_name
    return raw_name


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AiRXS2RebootSwitch(coordinator, entry)])


class AiRXS2RebootSwitch(CoordinatorEntity, SwitchEntity):
    """Switch-shaped reboot control matching the SSH integration's UI."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._entry = entry
        self._name = _display_name(entry.data["name"])
        self._attr_name = f"{self._name} Reboot"
        # Keep the SSH integration's unique ID for continuity.
        self._attr_unique_id = f"{entry.data['host']}_reboot"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["host"])},
            name=self._name,
            manufacturer="Ubiquiti",
            model="Ubiquiti AirOS",
            configuration_url=self.coordinator.host.rstrip("/"),
        )

    async def async_turn_on(self, **kwargs):
        """Request a normal reboot over the HTTP interface."""
        await self.coordinator.async_reboot()

    async def async_turn_off(self, **kwargs):
        """The reboot control is momentary; turning it off does nothing."""

    @property
    def is_on(self):
        """A reboot command is momentary, so the switch returns to off."""
        return False
