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
async def test_turn_off_automation_prevents_actions(hass: HomeAssistant):
    calls = async_mock_service(hass, "persistent_notification", "create")
    await _setup_automations(hass)

    # entity_id derived from alias -> "automation.tasks_updated"
    await hass.services.async_call(
        "automation",
        "turn_off",
        {"entity_id": "automation.tasks_updated"},
        blocking=True,
    )

    hass.states.async_set(
        "sensor.google_tasks", "1", {"last_updated": "t0", "tasks": ["gym"]}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "sensor.google_tasks", "2", {"last_updated": "t1", "tasks": ["gym", "buy milk"]}
    )
    await hass.async_block_till_done()

    assert len(calls) == 0