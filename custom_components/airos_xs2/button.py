"""Maintenance controls for legacy airOS devices."""
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, device_identifier


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AirOSRebootButton(coordinator, entry)])


class AirOSRebootButton(CoordinatorEntity, ButtonEntity):
    """Button to reboot the device without factory-resetting it."""

    _attr_has_entity_name = True
    _attr_name = "Reboot"
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data['host']}_reboot"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_identifier(entry.data["host"]))},
            manufacturer="Ubiquiti",
            model="Original airOS 3.x–4.x",
            name=entry.data["name"],
            configuration_url=coordinator.host.rstrip("/"),
        )
        self._coordinator = coordinator

    async def async_press(self):
        """Request a normal reboot over the device's HTTP interface."""
        await self._coordinator.async_reboot()
