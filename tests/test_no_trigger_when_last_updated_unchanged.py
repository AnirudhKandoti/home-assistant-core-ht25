import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from tests.common import async_mock_service


async def _setup_automations(hass: HomeAssistant):
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
async def test_no_trigger_when_last_updated_unchanged(hass: HomeAssistant):
    calls = async_mock_service(hass, "persistent_notification", "create")
    await _setup_automations(hass)

    hass.states.async_set(
        "sensor.google_tasks", "1", {"last_updated": "t0", "tasks": ["gym"]}
    )
    await hass.async_block_till_done()
    baseline = len(calls)

    # Change state and tasks, but keep last_updated the same → should NOT fire
    hass.states.async_set(
        "sensor.google_tasks",
        "999",
        {"last_updated": "t0", "tasks": ["gym", "buy milk"]},
    )
    await hass.async_block_till_done()

    assert len(calls) == baseline