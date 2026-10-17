import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN


class AiRXS2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            host = user_input["host"].strip().rstrip("/")
            if not host.startswith(("http://", "https://")):
                host = "http://" + host
            data = {**user_input, "host": host}
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=data["name"], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name", default="AirOS"): str,
                vol.Required("host", description={"suggested_value": "http://192.168.1.20"}): str,
                vol.Required("username"): str,
                vol.Required("password"): str,
            }),
        )
