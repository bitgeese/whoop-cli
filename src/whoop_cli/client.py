from __future__ import annotations

from datetime import datetime
from typing import AsyncGenerator, TypeVar

import httpx

from whoop_cli.auth import get_access_token, refresh_access_token
from whoop_cli.config import API_BASE
from whoop_cli.models import (
    BodyMeasurement,
    Cycle,
    PaginatedResponse,
    Profile,
    Recovery,
    Sleep,
    Workout,
)

T = TypeVar("T")


class WhoopClient:
    def __init__(self, access_token: str) -> None:
        self._token = access_token
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> WhoopClient:
        self._client = httpx.AsyncClient(
            base_url=API_BASE,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        assert self._client is not None
        response = await self._client.request(method, path, **kwargs)

        if response.status_code == 401:
            new_token = refresh_access_token()
            if new_token:
                self._token = new_token
                self._client.headers["Authorization"] = f"Bearer {new_token}"
                response = await self._client.request(method, path, **kwargs)

        if response.status_code == 401:
            raise SystemExit("Session expired. Run `whoop auth login` to re-authenticate.")

        response.raise_for_status()
        return response

    async def _paginate(
        self,
        path: str,
        params: dict | None = None,
    ) -> AsyncGenerator[dict, None]:
        params = dict(params or {})
        while True:
            response = await self._request("GET", path, params=params)
            data = response.json()
            for record in data.get("records", []):
                yield record
            next_token = data.get("next_token")
            if not next_token:
                break
            params["nextToken"] = next_token

    # --- Typed API methods ---

    async def get_profile(self) -> Profile:
        resp = await self._request("GET", "/v2/user/profile/basic")
        return Profile.model_validate(resp.json())

    async def get_body_measurement(self) -> BodyMeasurement:
        resp = await self._request("GET", "/v2/user/measurement/body")
        return BodyMeasurement.model_validate(resp.json())

    async def get_cycles(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> list[Cycle]:
        params: dict[str, str] = {}
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        records = []
        async for record in self._paginate("/v2/cycle", params):
            records.append(Cycle.model_validate(record))
        return records

    async def get_recovery(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> list[Recovery]:
        params: dict[str, str] = {}
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        records = []
        async for record in self._paginate("/v2/recovery", params):
            records.append(Recovery.model_validate(record))
        return records

    async def get_sleep(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> list[Sleep]:
        params: dict[str, str] = {}
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        records = []
        async for record in self._paginate("/v2/activity/sleep", params):
            records.append(Sleep.model_validate(record))
        return records

    async def get_workouts(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> list[Workout]:
        params: dict[str, str] = {}
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        records = []
        async for record in self._paginate("/v2/activity/workout", params):
            records.append(Workout.model_validate(record))
        return records


def get_client() -> WhoopClient:
    token = get_access_token()
    if not token:
        raise SystemExit("Not authenticated. Run `whoop auth login` first.")
    return WhoopClient(token)
