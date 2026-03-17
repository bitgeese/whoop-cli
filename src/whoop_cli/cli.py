from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

import typer

from whoop_cli import __version__
from whoop_cli.client import get_client
from whoop_cli.formatters import format_json, ms_to_human, output, pct

app = typer.Typer(
    name="whoop",
    help="CLI tool to pull Whoop health data from the terminal.",
    no_args_is_help=True,
)

auth_app = typer.Typer(help="Manage Whoop authentication.")
app.add_typer(auth_app, name="auth")

# --- Global options ---

FormatOption = typer.Option(None, "--format", "-f", help="Output format: json, md, csv")


def version_callback(value: bool) -> None:
    if value:
        print(f"whoop-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-V", callback=version_callback, is_eager=True),
) -> None:
    pass


# --- Date helpers ---


def resolve_period(period: str) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    match period.lower():
        case "today":
            return today_start, now
        case "yesterday":
            return today_start - timedelta(days=1), today_start
        case "week":
            return today_start - timedelta(days=7), now
        case "month":
            return today_start - timedelta(days=30), now
        case _:
            raise typer.BadParameter(f"Unknown period: {period}. Use today/yesterday/week/month.")


def resolve_dates(
    period: str | None,
    start: str | None,
    end: str | None,
) -> tuple[datetime, datetime]:
    if period:
        return resolve_period(period)
    now = datetime.now(timezone.utc)
    s = datetime.fromisoformat(start) if start else now - timedelta(days=7)
    e = datetime.fromisoformat(end) if end else now
    if s.tzinfo is None:
        s = s.replace(tzinfo=timezone.utc)
    if e.tzinfo is None:
        e = e.replace(tzinfo=timezone.utc)
    return s, e


# --- Auth commands ---


@auth_app.command()
def login() -> None:
    """Authenticate with Whoop via OAuth 2.0 browser flow."""
    from whoop_cli.auth import start_oauth_flow

    try:
        start_oauth_flow()
        print("Authenticated successfully!")
    except Exception as e:
        print(f"Authentication failed: {e}")
        raise typer.Exit(1)


@auth_app.command()
def status() -> None:
    """Show current authentication status."""
    from whoop_cli.auth import get_access_token

    token = get_access_token()
    if token:
        print("Authenticated (token stored)")
    else:
        print("Not authenticated. Run `whoop auth login`.")


@auth_app.command()
def logout() -> None:
    """Clear stored Whoop tokens."""
    from whoop_cli.auth import clear_tokens

    clear_tokens()
    print("Logged out.")


# --- Data commands ---


@app.command()
def profile(fmt: Optional[str] = FormatOption) -> None:
    """Show your Whoop profile and body measurements."""

    async def _run() -> None:
        async with get_client() as client:
            p = await client.get_profile()
            b = await client.get_body_measurement()
            data = {**p.model_dump(mode="json"), **b.model_dump(mode="json")}
            output(data, fmt, title="Profile")

    asyncio.run(_run())


@app.command()
def sleep(
    period: Optional[str] = typer.Argument(None, help="today, yesterday, week, month"),
    start: Optional[str] = typer.Option(None, "--from", help="Start date (ISO 8601)"),
    end: Optional[str] = typer.Option(None, "--to", help="End date (ISO 8601)"),
    fmt: Optional[str] = FormatOption,
) -> None:
    """Show sleep data for a period or date range."""
    s, e = resolve_dates(period, start, end)

    async def _run() -> None:
        async with get_client() as client:
            records = await client.get_sleep(start=s, end=e)
            if not records:
                print("No sleep data found for this period.")
                raise typer.Exit()
            if len(records) == 1 and (fmt is None or fmt == "md"):
                _print_sleep_summary(records[0], fmt)
            else:
                output(records, fmt, title="Sleep")

    asyncio.run(_run())


def _print_sleep_summary(s: object, fmt: str | None) -> None:
    from whoop_cli.models import Sleep

    assert isinstance(s, Sleep)
    sc = s.score
    data = {
        "date": s.start.strftime("%Y-%m-%d"),
        "nap": s.nap,
        "score_state": s.score_state,
    }
    if sc:
        ss = sc.stage_summary
        data.update({
            "performance": pct(sc.sleep_performance_percentage),
            "efficiency": pct(sc.sleep_efficiency_percentage),
            "consistency": pct(sc.sleep_consistency_percentage),
            "respiratory_rate": f"{sc.respiratory_rate:.1f}" if sc.respiratory_rate else "-",
        })
        if ss:
            data.update({
                "total_in_bed": ms_to_human(ss.total_in_bed_time_milli),
                "awake": ms_to_human(ss.total_awake_time_milli),
                "light": ms_to_human(ss.total_light_sleep_time_milli),
                "sws": ms_to_human(ss.total_slow_wave_sleep_time_milli),
                "rem": ms_to_human(ss.total_rem_sleep_time_milli),
                "disturbances": ss.disturbance_count,
            })
    output(data, fmt, title="Sleep")


@app.command()
def recovery(
    period: Optional[str] = typer.Argument(None, help="today, yesterday, week, month"),
    start: Optional[str] = typer.Option(None, "--from", help="Start date (ISO 8601)"),
    end: Optional[str] = typer.Option(None, "--to", help="End date (ISO 8601)"),
    fmt: Optional[str] = FormatOption,
) -> None:
    """Show recovery data for a period or date range."""
    s, e = resolve_dates(period, start, end)

    async def _run() -> None:
        async with get_client() as client:
            records = await client.get_recovery(start=s, end=e)
            if not records:
                print("No recovery data found for this period.")
                raise typer.Exit()
            if len(records) == 1 and (fmt is None or fmt == "md"):
                _print_recovery_summary(records[0], fmt)
            else:
                output(records, fmt, title="Recovery")

    asyncio.run(_run())


def _print_recovery_summary(r: object, fmt: str | None) -> None:
    from whoop_cli.models import Recovery

    assert isinstance(r, Recovery)
    sc = r.score
    data: dict = {"score_state": r.score_state}
    if sc:
        data.update({
            "recovery_score": pct(sc.recovery_score),
            "hrv": f"{sc.hrv_rmssd_milli:.1f} ms" if sc.hrv_rmssd_milli else "-",
            "resting_hr": f"{sc.resting_heart_rate:.0f} bpm" if sc.resting_heart_rate else "-",
            "spo2": pct(sc.spo2_percentage),
            "skin_temp": f"{sc.skin_temp_celsius:.1f}°C" if sc.skin_temp_celsius else "-",
        })
    output(data, fmt, title="Recovery")


@app.command()
def strain(
    period: Optional[str] = typer.Argument(None, help="today, yesterday, week, month"),
    start: Optional[str] = typer.Option(None, "--from", help="Start date (ISO 8601)"),
    end: Optional[str] = typer.Option(None, "--to", help="End date (ISO 8601)"),
    fmt: Optional[str] = FormatOption,
) -> None:
    """Show strain/cycle data for a period or date range."""
    s, e = resolve_dates(period, start, end)

    async def _run() -> None:
        async with get_client() as client:
            records = await client.get_cycles(start=s, end=e)
            if not records:
                print("No cycle data found for this period.")
                raise typer.Exit()
            output(records, fmt, title="Strain")

    asyncio.run(_run())


@app.command()
def workouts(
    period: Optional[str] = typer.Argument(None, help="today, yesterday, week, month"),
    start: Optional[str] = typer.Option(None, "--from", help="Start date (ISO 8601)"),
    end: Optional[str] = typer.Option(None, "--to", help="End date (ISO 8601)"),
    fmt: Optional[str] = FormatOption,
) -> None:
    """Show workouts for a period or date range."""
    s, e = resolve_dates(period, start, end)

    async def _run() -> None:
        async with get_client() as client:
            records = await client.get_workouts(start=s, end=e)
            if not records:
                print("No workouts found for this period.")
                raise typer.Exit()
            output(records, fmt, title="Workouts")

    asyncio.run(_run())


@app.command()
def cycles(
    start: Optional[str] = typer.Option(None, "--from", help="Start date (ISO 8601)"),
    end: Optional[str] = typer.Option(None, "--to", help="End date (ISO 8601)"),
    fmt: Optional[str] = FormatOption,
) -> None:
    """Show physiological cycles for a date range."""
    s, e = resolve_dates(None, start, end)

    async def _run() -> None:
        async with get_client() as client:
            records = await client.get_cycles(start=s, end=e)
            if not records:
                print("No cycle data found.")
                raise typer.Exit()
            output(records, fmt, title="Cycles")

    asyncio.run(_run())


@app.command()
def summary(
    period: str = typer.Argument("today", help="today, yesterday, week, month"),
    fmt: Optional[str] = FormatOption,
) -> None:
    """Combined summary: sleep + recovery + strain."""
    s, e = resolve_dates(period, None, None)

    async def _run() -> None:
        async with get_client() as client:
            sleeps = await client.get_sleep(start=s, end=e)
            recoveries = await client.get_recovery(start=s, end=e)
            cycles_ = await client.get_cycles(start=s, end=e)

            data = {
                "period": period,
                "sleep": [sl.model_dump(mode="json") for sl in sleeps],
                "recovery": [r.model_dump(mode="json") for r in recoveries],
                "cycles": [c.model_dump(mode="json") for c in cycles_],
            }

            if fmt == "md" or (fmt is None and __import__("sys").stdout.isatty()):
                _print_summary_md(sleeps, recoveries, cycles_)
            else:
                output(data, fmt or "json")

    asyncio.run(_run())


def _print_summary_md(sleeps: list, recoveries: list, cycles_: list) -> None:
    from whoop_cli.models import Cycle, Recovery, Sleep

    lines: list[str] = []

    if recoveries:
        lines.append("## Recovery")
        for r in recoveries:
            assert isinstance(r, Recovery)
            sc = r.score
            if sc:
                lines.append(
                    f"- Score: {pct(sc.recovery_score)} | "
                    f"HRV: {sc.hrv_rmssd_milli:.1f} ms | "
                    f"RHR: {sc.resting_heart_rate:.0f} bpm"
                    if sc.hrv_rmssd_milli and sc.resting_heart_rate
                    else f"- Score: {pct(sc.recovery_score)}"
                )

    if sleeps:
        lines.append("\n## Sleep")
        for s in sleeps:
            assert isinstance(s, Sleep)
            sc = s.score
            if sc and sc.stage_summary:
                ss = sc.stage_summary
                lines.append(
                    f"- {s.start.strftime('%Y-%m-%d')}: "
                    f"Performance {pct(sc.sleep_performance_percentage)} | "
                    f"In bed {ms_to_human(ss.total_in_bed_time_milli)} | "
                    f"REM {ms_to_human(ss.total_rem_sleep_time_milli)} | "
                    f"SWS {ms_to_human(ss.total_slow_wave_sleep_time_milli)}"
                )

    if cycles_:
        lines.append("\n## Strain")
        for c in cycles_:
            assert isinstance(c, Cycle)
            sc = c.score
            if sc:
                lines.append(
                    f"- {c.start.strftime('%Y-%m-%d')}: "
                    f"Strain {sc.strain:.1f} | "
                    f"{sc.kilojoule:.0f} kJ | "
                    f"Avg HR {sc.average_heart_rate} bpm"
                    if sc.strain and sc.kilojoule and sc.average_heart_rate
                    else f"- {c.start.strftime('%Y-%m-%d')}: Strain {sc.strain}"
                )

    print("\n".join(lines) if lines else "No data found.")


@app.command()
def export(
    start: str = typer.Option(..., "--from", help="Start date (ISO 8601)"),
    end: Optional[str] = typer.Option(None, "--to", help="End date (ISO 8601)"),
    fmt: str = typer.Option("json", "--format", "-f", help="Output format: json, md, csv"),
) -> None:
    """Export all Whoop data for a date range."""
    s, e = resolve_dates(None, start, end)

    async def _run() -> None:
        async with get_client() as client:
            sleeps = await client.get_sleep(start=s, end=e)
            recoveries = await client.get_recovery(start=s, end=e)
            cycles_ = await client.get_cycles(start=s, end=e)
            workouts_ = await client.get_workouts(start=s, end=e)

            data = {
                "exported_from": start,
                "exported_to": end or "now",
                "sleep": [sl.model_dump(mode="json") for sl in sleeps],
                "recovery": [r.model_dump(mode="json") for r in recoveries],
                "cycles": [c.model_dump(mode="json") for c in cycles_],
                "workouts": [w.model_dump(mode="json") for w in workouts_],
            }

            if fmt == "csv":
                # For CSV, export each type separately
                from whoop_cli.formatters import format_csv

                if sleeps:
                    print("# Sleep")
                    print(format_csv(sleeps), end="")
                if recoveries:
                    print("\n# Recovery")
                    print(format_csv(recoveries), end="")
                if cycles_:
                    print("\n# Cycles")
                    print(format_csv(cycles_), end="")
                if workouts_:
                    print("\n# Workouts")
                    print(format_csv(workouts_), end="")
            else:
                output(data, fmt)

    asyncio.run(_run())
