import pytest


@pytest.fixture
def sample_profile():
    return {
        "user_id": 12345,
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def sample_body():
    return {
        "height_meter": 1.80,
        "weight_kilogram": 75.0,
        "max_heart_rate": 195,
    }


@pytest.fixture
def sample_recovery():
    return {
        "records": [
            {
                "cycle_id": 1,
                "sleep_id": 1,
                "user_id": 12345,
                "score_state": "SCORED",
                "score": {
                    "user_calibrating": False,
                    "recovery_score": 78.0,
                    "resting_heart_rate": 52.0,
                    "hrv_rmssd_milli": 45.3,
                    "spo2_percentage": 97.0,
                    "skin_temp_celsius": 33.5,
                },
                "created_at": "2026-03-16T06:00:00Z",
                "updated_at": "2026-03-16T06:00:00Z",
            }
        ],
        "next_token": None,
    }


@pytest.fixture
def sample_sleep():
    return {
        "records": [
            {
                "id": 1,
                "user_id": 12345,
                "start": "2026-03-15T23:00:00Z",
                "end": "2026-03-16T07:00:00Z",
                "nap": False,
                "score_state": "SCORED",
                "score": {
                    "stage_summary": {
                        "total_in_bed_time_milli": 28800000,
                        "total_awake_time_milli": 3600000,
                        "total_light_sleep_time_milli": 10800000,
                        "total_slow_wave_sleep_time_milli": 7200000,
                        "total_rem_sleep_time_milli": 5400000,
                        "total_no_data_time_milli": 0,
                        "sleep_cycle_count": 5,
                        "disturbance_count": 12,
                    },
                    "sleep_needed": {
                        "baseline_milli": 28800000,
                        "need_from_sleep_debt_milli": 0,
                        "need_from_recent_strain_milli": 1800000,
                        "need_from_recent_nap_milli": 0,
                    },
                    "respiratory_rate": 15.2,
                    "sleep_performance_percentage": 85.0,
                    "sleep_consistency_percentage": 90.0,
                    "sleep_efficiency_percentage": 88.0,
                },
            }
        ],
        "next_token": None,
    }


@pytest.fixture
def sample_cycle():
    return {
        "records": [
            {
                "id": 1,
                "user_id": 12345,
                "start": "2026-03-16T00:00:00Z",
                "end": "2026-03-17T00:00:00Z",
                "score_state": "SCORED",
                "score": {
                    "strain": 12.5,
                    "kilojoule": 8500.0,
                    "average_heart_rate": 72,
                    "max_heart_rate": 165,
                },
            }
        ],
        "next_token": None,
    }


@pytest.fixture
def sample_workout():
    return {
        "records": [
            {
                "id": 1,
                "user_id": 12345,
                "start": "2026-03-16T08:00:00Z",
                "end": "2026-03-16T09:00:00Z",
                "sport_id": 1,
                "score_state": "SCORED",
                "score": {
                    "strain": 8.5,
                    "average_heart_rate": 145,
                    "max_heart_rate": 175,
                    "kilojoule": 1200.0,
                    "percent_recorded": 100.0,
                    "distance_meter": 5000.0,
                    "altitude_gain_meter": 50.0,
                    "altitude_change_meter": 10.0,
                    "zone_duration": {
                        "zone_zero_milli": 60000,
                        "zone_one_milli": 300000,
                        "zone_two_milli": 600000,
                        "zone_three_milli": 1200000,
                        "zone_four_milli": 900000,
                        "zone_five_milli": 300000,
                    },
                },
            }
        ],
        "next_token": None,
    }
