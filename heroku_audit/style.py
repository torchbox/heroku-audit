from typing import TYPE_CHECKING, Optional

from rich.console import RenderableType
from rich.text import Text

if TYPE_CHECKING:
    from heroku_audit.cli.postgres import HerokuBackupSchedule


def style_user_role(role: Optional[str]) -> RenderableType:
    if role == "admin":
        return Text(role, style="red")
    elif role == "member":
        return Text(role, style="purple")
    elif role is None:
        return "collaborator"
    return role


def style_dyno_formation_size(formation_size: str) -> RenderableType:
    if formation_size == "Basic":
        return Text(formation_size, style="purple")
    return formation_size


def style_dyno_formation_quantity(quantity: int) -> RenderableType:
    if quantity == 0:
        return Text("Stopped", style="red")
    return str(quantity)


def style_backup_schedules(schedules: list["HerokuBackupSchedule"]) -> RenderableType:
    if not schedules:
        return Text("None", style="red")

    return ", ".join(f"Daily at {s['hour']}:00 {s['timezone']}" for s in schedules)


def style_maintenance_window(maintenance_window: Optional[str]) -> RenderableType:
    if maintenance_window is None:
        return Text("None", style="red")
    return maintenance_window


def style_acm_status(acm_status: Optional[str]) -> RenderableType:
    if acm_status is None:
        return ""
    if acm_status == "cert issued":
        return Text("Cert issued", style="green")
    elif acm_status == "failed":
        return Text("Failed", style="red")
    return acm_status


def style_hostname(hostname: str) -> RenderableType:
    if hostname.endswith("herokuapp.com"):
        return Text(hostname, style="purple")
    return Text(hostname)
