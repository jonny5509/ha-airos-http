import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN


def _device_schema(data=None):
    data = data or {}
    return vol.Schema({
        vol.Required("name", default=data.get("name", "NanoStation5")): str,
        vol.Required("host", default=data.get("host", "http://192.168.1.20")): str,
        vol.Required("username", default=data.get("username", "")): str,
        vol.Required("password", default=data.get("password", "")): str,
    })


class AiRXS2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # This legacy device is configured for plain HTTP only.
            host = user_input["host"].strip().rstrip("/")
            host = host.removeprefix("https://").removeprefix("http://").strip("/")
            host = "http://" + host
            data = {**user_input, "host": host}
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=data["name"], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_device_schema(),
        )

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            host = user_input["host"].strip().rstrip("/")
            host = host.removeprefix("https://").removeprefix("http://").strip("/")
            data = {**user_input, "host": "http://" + host}
            self.hass.config_entries.async_update_entry(
                entry, data=data, title=data["name"]
            )
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_device_schema(entry.data),
        )
