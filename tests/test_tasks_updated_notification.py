# tests/test_tasks_updated_notification.py
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from tests.common import async_mock_service


async def _setup_test_automations(hass: HomeAssistant) -> None:
    """Register minimal automations for this test file only."""
    cfg = {
        "automation": [
            {
                "alias": "Tasks Updated",
                "mode": "single",
                "trigger": [
                    {
                        "platform": "state",
                        "entity_id": "sensor.google_tasks",
                        "attribute": "last_updated",
                    }
                ],
                "action": [
                    {
                        "service": "persistent_notification.create",
                        "data": {
                            "title": "Tasks Updated",
                            "message": "You now have {{ states('sensor.google_tasks') }} task(s).",
                        },
                    }
                ],
            }
        ]
    }
    assert await async_setup_component(hass, "automation", cfg)
    await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_tasks_updated_notification(hass: HomeAssistant):
    # Arrange
    pn_calls = async_mock_service(hass, "persistent_notification", "create")
    await _setup_test_automations(hass)

    # Initial state
    hass.states.async_set(
        "sensor.google_tasks", "1", {"last_updated": "t0", "tasks": ["gym"]}
    )
    await hass.async_block_till_done()

    # Trigger: change the triggering attribute
    hass.states.async_set(
        "sensor.google_tasks", "2", {"last_updated": "t1", "tasks": ["gym", "buy milk"]}
    )
    await hass.async_block_till_done()

    # Assert
    assert len(pn_calls) >= 1
    assert pn_calls[-1].data["title"] == "Tasks Updated"
    assert "You now have 2 task(s)." in pn_calls[-1].data["message"]