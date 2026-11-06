import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


def _clean_host(value):
    host = value.strip().rstrip("/")
    host = host.removeprefix("https://").removeprefix("http://").strip("/")
    if not host:
        raise vol.Invalid("Host cannot be empty")
    return host


def _device_schema(data=None):
    data = data or {}
    return vol.Schema({
        vol.Required("name", default=data.get("name", "NanoStation5")): vol.All(str, vol.Length(min=1)),
        vol.Required("host", default=_clean_host(data.get("host", "192.168.1.20"))): vol.All(str, vol.Length(min=1)),
        vol.Required("username", default=data.get("username", "")): vol.All(str, vol.Length(min=1)),
        vol.Required("password", default=data.get("password", "")): vol.All(str, vol.Length(min=1)),
    })


def _entry_data(user_input):
    host = _clean_host(user_input["host"])
    return {**user_input, "host": f"http://{host}"}


class AiRXS2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            data = _entry_data(user_input)
            await self.async_set_unique_id(data["host"].lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=data["name"], data=data)

        return self.async_show_form(step_id="user", data_schema=_device_schema())

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            data = _entry_data(user_input)
            self.hass.config_entries.async_update_entry(entry, data=data, title=data["name"])
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_device_schema(entry.data),
        )
}
