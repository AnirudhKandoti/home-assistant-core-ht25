# tests/test_automations_google_tasks.py
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from tests.common import async_mock_service


# Helper: set up two automations inline so pytest doesn't rely on external YAML.
# 1) "Tasks Updated": fires when sensor.google_tasks last_updated changes -> persistent_notification
# 2) "Weather vs Tasks": fires on same trigger, but only if rainy AND "gym" is in tasks list
async def _setup_test_automations(hass: HomeAssistant) -> None:
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
                        # treat "gym" as outdoor task; adapt this to your real rule
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
async def test_tasks_updated_notification(hass: HomeAssistant):
    # Mock both domains just in case your actions change later
    pn_calls = async_mock_service(hass, "persistent_notification", "create")
    notify_calls = async_mock_service(hass, "notify", "notify")

    await _setup_test_automations(hass)

    # Initial state
    hass.states.async_set(
        "sensor.google_tasks",
        "1",
        {"last_updated": "2025-10-23T18:00:00Z", "tasks": ["gym"]},
    )
    await hass.async_block_till_done()

    # Trigger by changing the triggering attribute
    hass.states.async_set(
        "sensor.google_tasks",
        "2",
        {"last_updated": "2025-10-23T18:05:00Z", "tasks": ["gym", "buy milk"]},
    )
    await hass.async_block_till_done()

    # Assert: at least one action fired and message text matches
    assert len(pn_calls) >= 1 or len(notify_calls) >= 1
    if pn_calls:
        assert "You now have 2 task(s)." in pn_calls[-1].data["message"]


@pytest.mark.asyncio
async def test_weather_vs_tasks_headsup(hass: HomeAssistant):
    pn_calls = async_mock_service(hass, "persistent_notification", "create")
    notify_calls = async_mock_service(hass, "notify", "notify")

    await _setup_test_automations(hass)

    # Set condition entities first
    hass.states.async_set("weather.home", "rainy", {})
    hass.states.async_set(
        "sensor.google_tasks",
        "1",
        {"last_updated": "2025-10-23T18:00:00Z", "tasks": ["gym"]},
    )
    await hass.async_block_till_done()

    # Change the triggering attribute again
    hass.states.async_set(
        "sensor.google_tasks",
        "2",
        {"last_updated": "2025-10-23T18:10:00Z", "tasks": ["gym", "buy milk"]},
    )
    await hass.async_block_till_done()

    # Assert: heads-up notification appeared
    titles = [c.data.get("title", "") for c in pn_calls] + [
        c.data.get("title", "") for c in notify_calls
    ]
    assert any("Heads up: Weather vs Tasks" in t for t in titles)