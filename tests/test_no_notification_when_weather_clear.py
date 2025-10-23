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
            },
            {
                "alias": "Heads up: Weather vs Tasks",
                "mode": "single",
                "trigger": [
                    {
                        "platform": "state",
                        "entity_id": "sensor.google_tasks",
                        "attribute": "last_updated",
                    }
                ],
                "condition": [
                    {
                        "condition": "template",
                        "value_template": "{{ states('weather.home') in ['rainy','pouring'] }}",
                    },
                    {
                        "condition": "template",
                        "value_template": "{{ 'gym' in (state_attr('sensor.google_tasks','tasks') or []) }}",
                    },
                ],
                "action": [
                    {
                        "service": "persistent_notification.create",
                        "data": {
                            "title": "Heads up: Weather vs Tasks",
                            "message": "Outdoor task detected (gym) and weather is rainy.",
                        },
                    }
                ],
            },
        ]
    }
    assert await async_setup_component(hass, "automation", cfg)
    await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_no_heads_up_when_weather_clear(hass: HomeAssistant):
    calls = async_mock_service(hass, "persistent_notification", "create")
    await _setup_automations(hass)

    hass.states.async_set("weather.home", "clear", {})
    hass.states.async_set(
        "sensor.google_tasks", "1", {"last_updated": "t0", "tasks": ["gym"]}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "sensor.google_tasks", "2", {"last_updated": "t1", "tasks": ["gym"]}
    )
    await hass.async_block_till_done()

    titles = [c.data.get("title", "") for c in calls]
    assert "Heads up: Weather vs Tasks" not in titles  # heads-up must NOT appear
    assert any(t == "Tasks Updated" for t in titles)  # generic one can appear