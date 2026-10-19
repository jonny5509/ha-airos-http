"""Mocked HTTP-path tests for the legacy airOS coordinator."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import aiohttp
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.airos_xs2.coordinator import AiRXS2Coordinator


def coordinator_for_test():
    """Build a coordinator without opening a real network session."""
    coordinator = AiRXS2Coordinator.__new__(AiRXS2Coordinator)
    coordinator.host = "http://192.0.2.10/"
    coordinator.username = "test-user"
    coordinator.password = "test-password"
    coordinator.device_name = "Test radio"
    coordinator._login = AsyncMock()
    coordinator._request = AsyncMock()
    return coordinator


@pytest.mark.asyncio
async def test_update_data_logs_in_and_parses_status():
    coordinator = coordinator_for_test()
    coordinator._request.side_effect = [
        '{"signal": -63, "noise": -96, "essid": "TestNet"}',
        '<input name="hostname" value="roof-radio">',
    ]

    data = await coordinator._async_update_data()

    coordinator._login.assert_awaited_once_with()
    assert coordinator._request.await_args_list[0].args == ("status.cgi",)
    assert coordinator._request.await_args_list[1].args == ("system.cgi",)
    assert data["signal"] == -63
    assert data["noise"] == -96
    assert data["snr"] == 33
    assert data["essid"] == "TestNet"
    assert data["hostname"] == "roof-radio"


@pytest.mark.asyncio
async def test_update_data_surfaces_status_http_failure():
    coordinator = coordinator_for_test()
    coordinator._request.side_effect = UpdateFailed("airOS HTTP 500 from status.cgi")

    with pytest.raises(UpdateFailed, match="HTTP 500"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_update_data_wraps_network_errors():
    coordinator = coordinator_for_test()
    coordinator._request.side_effect = aiohttp.ClientConnectionError("connection refused")

    with pytest.raises(UpdateFailed, match="Could not connect"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_reboot_requests_only_normal_reboot_endpoint():
    coordinator = coordinator_for_test()

    await coordinator.async_reboot()

    coordinator._login.assert_awaited_once_with()
    coordinator._request.assert_awaited_once_with("reboot.cgi")
    assert all(call.args[0] != "reset.cgi" for call in coordinator._request.await_args_list)


@pytest.mark.asyncio
async def test_reboot_tolerates_connection_drop_during_restart():
    coordinator = coordinator_for_test()
    coordinator._request.side_effect = aiohttp.ClientConnectionError("device restarting")

    await coordinator.async_reboot()

    coordinator._login.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_setup_closes_session_when_first_refresh_fails(monkeypatch):
    import custom_components.airos_xs2 as integration

    coordinator = SimpleNamespace(
        async_config_entry_first_refresh=AsyncMock(side_effect=UpdateFailed("login failed")),
        async_close=AsyncMock(),
        data=None,
    )
    monkeypatch.setattr(integration, "AiRXS2Coordinator", lambda *args: coordinator)
    hass = SimpleNamespace(data={}, config_entries=SimpleNamespace())
    entry = SimpleNamespace(
        data={"host": "http://192.0.2.10/", "username": "u", "password": "p", "name": "Radio"},
        entry_id="entry-1",
    )

    with pytest.raises(UpdateFailed, match="login failed"):
        await integration.async_setup_entry(hass, entry)

    coordinator.async_close.assert_awaited_once_with()
    assert "airos_xs2" not in hass.data
