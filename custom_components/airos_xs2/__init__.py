"""Home Assistant integration for legacy Ubiquiti airOS devices over SSH or HTTP."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AiRXS2Coordinator as HttpCoordinator
from .coordinator_ssh import AiRXS2Coordinator as SshCoordinator

PLATFORMS = ["sensor", "button", "switch"]

_AUTO_NAMES = {
    "airos", "air os", "ubiquiti airos", "ubiquiti airos (http)",
    "ubiquiti airos (ssh)", "nanostation5",
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    protocol = entry.data.get("protocol") or ("http" if entry.data.get("host", "").lower().startswith(("http://", "https://")) else "ssh")
    protocol = protocol.lower()
    coordinator_class = SshCoordinator if protocol == "ssh" else HttpCoordinator
    coordinator = coordinator_class(
        hass, entry.data["host"], entry.data["username"],
        entry.data["password"], entry.data["name"],
    )
    try:
        await coordinator.async_config_entry_first_refresh()
        current_name = entry.data.get("name", "").strip()
        hostname = str((coordinator.data or {}).get("hostname", "")).strip()
        if protocol == "http" and current_name.lower() in _AUTO_NAMES:
            detected_name = hostname or "NanoStation5"
            if detected_name != current_name:
                hass.config_entries.async_update_entry(
                    entry, data={**entry.data, "name": detected_name},
                    title=detected_name,
                )
                coordinator.device_name = detected_name

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except BaseException:
        close = getattr(coordinator, "async_close", None)
        if close:
            await close()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        raise


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        close = getattr(coordinator, "async_close", None)
        if close:
            await close()
    return unloaded
