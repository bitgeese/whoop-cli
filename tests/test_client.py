import pytest
import respx
from httpx import Response

from whoop_cli.client import WhoopClient
from whoop_cli.config import API_BASE


@pytest.mark.asyncio
async def test_get_profile(sample_profile):
    with respx.mock:
        respx.get(f"{API_BASE}/v1/user/profile/basic").mock(
            return_value=Response(200, json=sample_profile)
        )
        async with WhoopClient("test-token") as client:
            profile = await client.get_profile()
            assert profile.email == "test@example.com"
            assert profile.first_name == "Test"


@pytest.mark.asyncio
async def test_get_body_measurement(sample_body):
    with respx.mock:
        respx.get(f"{API_BASE}/v1/user/measurement/body").mock(
            return_value=Response(200, json=sample_body)
        )
        async with WhoopClient("test-token") as client:
            body = await client.get_body_measurement()
            assert body.height_meter == 1.80
            assert body.max_heart_rate == 195


@pytest.mark.asyncio
async def test_get_recovery(sample_recovery):
    with respx.mock:
        respx.get(f"{API_BASE}/v1/recovery").mock(
            return_value=Response(200, json=sample_recovery)
        )
        async with WhoopClient("test-token") as client:
            records = await client.get_recovery()
            assert len(records) == 1
            assert records[0].score.recovery_score == 78.0
            assert records[0].score.hrv_rmssd_milli == 45.3


@pytest.mark.asyncio
async def test_get_sleep(sample_sleep):
    with respx.mock:
        respx.get(f"{API_BASE}/v1/sleep").mock(
            return_value=Response(200, json=sample_sleep)
        )
        async with WhoopClient("test-token") as client:
            records = await client.get_sleep()
            assert len(records) == 1
            assert records[0].score.sleep_performance_percentage == 85.0


@pytest.mark.asyncio
async def test_get_cycles(sample_cycle):
    with respx.mock:
        respx.get(f"{API_BASE}/v1/cycle").mock(
            return_value=Response(200, json=sample_cycle)
        )
        async with WhoopClient("test-token") as client:
            records = await client.get_cycles()
            assert len(records) == 1
            assert records[0].score.strain == 12.5


@pytest.mark.asyncio
async def test_get_workouts(sample_workout):
    with respx.mock:
        respx.get(f"{API_BASE}/v1/workout").mock(
            return_value=Response(200, json=sample_workout)
        )
        async with WhoopClient("test-token") as client:
            records = await client.get_workouts()
            assert len(records) == 1
            assert records[0].score.strain == 8.5
            assert records[0].score.distance_meter == 5000.0


@pytest.mark.asyncio
async def test_pagination():
    page1 = {
        "records": [
            {
                "cycle_id": 1, "sleep_id": 1, "user_id": 1,
                "score_state": "SCORED", "score": {"recovery_score": 70.0},
            }
        ],
        "next_token": "page2",
    }
    page2 = {
        "records": [
            {
                "cycle_id": 2, "sleep_id": 2, "user_id": 1,
                "score_state": "SCORED", "score": {"recovery_score": 80.0},
            }
        ],
        "next_token": None,
    }

    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if "nextToken" in str(request.url):
            return Response(200, json=page2)
        return Response(200, json=page1)

    with respx.mock:
        respx.get(f"{API_BASE}/v1/recovery").mock(side_effect=side_effect)
        async with WhoopClient("test-token") as client:
            records = await client.get_recovery()
            assert len(records) == 2
            assert records[0].score.recovery_score == 70.0
            assert records[1].score.recovery_score == 80.0
            assert call_count == 2


@pytest.mark.asyncio
async def test_401_retry(sample_profile, monkeypatch):
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return Response(401, json={"error": "Unauthorized"})
        return Response(200, json=sample_profile)

    monkeypatch.setattr("whoop_cli.client.refresh_access_token", lambda: "new-token")

    with respx.mock:
        respx.get(f"{API_BASE}/v1/user/profile/basic").mock(side_effect=side_effect)
        async with WhoopClient("old-token") as client:
            profile = await client.get_profile()
            assert profile.email == "test@example.com"
            assert call_count == 2
