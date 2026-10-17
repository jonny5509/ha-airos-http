from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AiRXS2Coordinator

PLATFORMS = ["sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Older setups used the generic "AirOS" label. Upgrade that default to the
    # actual hardware model without overriding a name the user chose themselves.
    current_name = entry.data.get("name", "").strip()
    if current_name.lower() in {"airos", "air os", "ubiquiti airos", "ubiquiti airos (http)"}:
        updated_data = {**entry.data, "name": "NanoStation5"}
        hass.config_entries.async_update_entry(
            entry, data=updated_data, title="NanoStation5"
        )

    coordinator = AiRXS2Coordinator(
        hass, entry.data["host"], entry.data["username"],
        entry.data["password"], entry.data["name"],
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_close()
    return unloaded
