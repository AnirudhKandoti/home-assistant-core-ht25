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
async def test_multiple_updates_fire_multiple_notifications(hass: HomeAssistant):
    calls = async_mock_service(hass, "persistent_notification", "create")
    await _setup_automations(hass)

    # Initial prime (this WILL trigger once because last_updated changes from None -> "t0")
    hass.states.async_set(
        "sensor.google_tasks", "0", {"last_updated": "t0", "tasks": []}
    )
    await hass.async_block_till_done()

    # Record baseline count after the initial trigger
    baseline = sum(1 for c in calls if c.data.get("title") == "Tasks Updated")

    # Now perform 3 updates -> expect +3 notifications over baseline
    for i in range(1, 4):
        hass.states.async_set(
            "sensor.google_tasks",
            str(i),
            {"last_updated": f"t{i}", "tasks": ["x"] * i},
        )
        await hass.async_block_till_done()

    total = sum(1 for c in calls if c.data.get("title") == "Tasks Updated")
    assert total - baseline == 3