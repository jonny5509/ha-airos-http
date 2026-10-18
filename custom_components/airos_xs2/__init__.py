"""Set up the Ubiquiti AirOS HTTP integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.importlib import async_import_module

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

# These are generic/default labels, not user-customised device names.
_AUTO_NAMES = {
    "airos",
    "air os",
    "ubiquiti airos",
    "ubiquiti airos (http)",
    "ubnt",
    "ubnt airos",
    "nanostation5",
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an AirOS device."""
    # The coordinator imports HTTP/parsing dependencies. Load it via Home
    # Assistant's import executor so legacy component setup cannot block the
    # event loop while importing the integration dependency tree.
    coordinator_module = await async_import_module(
        hass, f"{__package__}.coordinator"
    )
    coordinator = coordinator_module.AiRXS2Coordinator(
        hass,
        entry.data["host"],
        entry.data["username"],
        entry.data["password"],
        entry.data["name"],
    )
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        # The coordinator owns an aiohttp session; close it if initial setup fails
        # so Home Assistant's automatic setup retry does not leak sessions.
        await coordinator.async_close()
        raise

    # airOS 4 exposes its configured hostname on system.cgi. Use it to name
    # entries still using a generic integration/model default, while preserving
    # any name the user deliberately chose.
    current_name = entry.data.get("name", "").strip()
    hostname = str((coordinator.data or {}).get("hostname", "")).strip()
    if current_name.lower() in _AUTO_NAMES:
        detected_name = hostname or "NanoStation5"
        if detected_name != current_name:
            hass.config_entries.async_update_entry(
                entry,
                data={**entry.data, "name": detected_name},
                title=detected_name,
            )
            coordinator.device_name = detected_name

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an AirOS device."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if coordinator is not None:
            await coordinator.async_close()
        if not hass.data.get(DOMAIN):
            hass.data.pop(DOMAIN, None)
    return unloaded
