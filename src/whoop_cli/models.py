from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


# --- Profile ---


class Profile(StrictModel):
    user_id: int | str
    email: str
    first_name: str
    last_name: str


class BodyMeasurement(StrictModel):
    height_meter: float | None = None
    weight_kilogram: float | None = None
    max_heart_rate: int | None = None


# --- Cycles ---


class CycleScore(StrictModel):
    strain: float | None = None
    kilojoule: float | None = None
    average_heart_rate: int | None = None
    max_heart_rate: int | None = None


class Cycle(StrictModel):
    id: int | str
    user_id: int | str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    start: datetime
    end: datetime | None = None
    timezone_offset: str | None = None
    score_state: str
    score: CycleScore | None = None


# --- Recovery ---


class RecoveryScore(StrictModel):
    user_calibrating: bool | None = None
    recovery_score: float | None = None
    resting_heart_rate: float | None = None
    hrv_rmssd_milli: float | None = None
    spo2_percentage: float | None = None
    skin_temp_celsius: float | None = None


class Recovery(StrictModel):
    cycle_id: int | str
    sleep_id: int | str
    user_id: int | str
    score_state: str
    score: RecoveryScore | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# --- Sleep ---


class StageSummary(StrictModel):
    total_in_bed_time_milli: int | None = None
    total_awake_time_milli: int | None = None
    total_no_data_time_milli: int | None = None
    total_light_sleep_time_milli: int | None = None
    total_slow_wave_sleep_time_milli: int | None = None
    total_rem_sleep_time_milli: int | None = None
    sleep_cycle_count: int | None = None
    disturbance_count: int | None = None


class SleepNeeded(StrictModel):
    baseline_milli: int | None = None
    need_from_sleep_debt_milli: int | None = None
    need_from_recent_strain_milli: int | None = None
    need_from_recent_nap_milli: int | None = None


class SleepScore(StrictModel):
    stage_summary: StageSummary | None = None
    sleep_needed: SleepNeeded | None = None
    respiratory_rate: float | None = None
    sleep_performance_percentage: float | None = None
    sleep_consistency_percentage: float | None = None
    sleep_efficiency_percentage: float | None = None


class Sleep(StrictModel):
    id: int | str
    user_id: int | str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    start: datetime
    end: datetime | None = None
    timezone_offset: str | None = None
    nap: bool = False
    cycle_id: int | str | None = None
    score_state: str
    score: SleepScore | None = None


# --- Workouts ---


class ZoneDuration(StrictModel):
    zone_zero_milli: int | None = None
    zone_one_milli: int | None = None
    zone_two_milli: int | None = None
    zone_three_milli: int | None = None
    zone_four_milli: int | None = None
    zone_five_milli: int | None = None


class WorkoutScore(StrictModel):
    strain: float | None = None
    average_heart_rate: int | None = None
    max_heart_rate: int | None = None
    kilojoule: float | None = None
    percent_recorded: float | None = None
    distance_meter: float | None = None
    altitude_gain_meter: float | None = None
    altitude_change_meter: float | None = None
    zone_durations: ZoneDuration | None = None


class Workout(StrictModel):
    id: int | str
    user_id: int | str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    start: datetime
    end: datetime | None = None
    timezone_offset: str | None = None
    sport_id: int
    sport_name: str | None = None
    score_state: str
    score: WorkoutScore | None = None


# --- Pagination ---


class PaginatedResponse(StrictModel, Generic[T]):
    records: list[T]
    next_token: str | None = None
