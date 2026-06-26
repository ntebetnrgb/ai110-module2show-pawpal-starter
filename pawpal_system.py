"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes.

This module is the "brain" of PawPal+. It is fully independent of the
Streamlit UI so it can be exercised from a CLI demo (main.py) and pytest.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
import itertools
import json

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
VALID_FREQUENCIES = {"once", "daily", "weekly"}

_id_counter = itertools.count(1)


def _next_id() -> int:
    """Return a process-unique integer id for tasks and pets."""
    return next(_id_counter)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care activity (walk, feeding, meds, etc.)."""

    description: str
    time: str = "08:00"            # "HH:MM" 24-hour clock
    duration_minutes: int = 15
    priority: str = "medium"       # low | medium | high
    frequency: str = "once"        # once | daily | weekly
    due_date: str = field(default_factory=lambda: date.today().isoformat())
    completed: bool = False
    id: int = field(default_factory=_next_id)
    pet_name: str = ""             # stamped by Pet.add_task for scheduler reporting

    def __post_init__(self) -> None:
        """Validate user-supplied fields so bad data fails fast."""
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}")
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"priority must be one of {set(PRIORITY_ORDER)}")
        self._validate_time(self.time)

    @staticmethod
    def _validate_time(value: str) -> None:
        """Raise ValueError if value is not a valid HH:MM 24-hour time."""
        datetime.strptime(value, "%H:%M")

    @property
    def minutes_since_midnight(self) -> int:
        """Return the task time expressed as minutes after 00:00 for sorting."""
        h, m = self.time.split(":")
        return int(h) * 60 + int(m)

    @property
    def priority_rank(self) -> int:
        """Return a sortable rank where high=0 sorts before low=2."""
        return PRIORITY_ORDER[self.priority]

    def mark_complete(self) -> "Task | None":
        """Mark the task done; return the next occurrence if it recurs."""
        self.completed = True
        return self._spawn_next()

    def _spawn_next(self) -> "Task | None":
        """Create the next Task instance for a daily/weekly task, else None."""
        if self.frequency == "once":
            return None
        delta = timedelta(days=1 if self.frequency == "daily" else 7)
        next_due = date.fromisoformat(self.due_date) + delta
        return Task(
            description=self.description,
            time=self.time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            due_date=next_due.isoformat(),
            completed=False,
            pet_name=self.pet_name,
        )

    def __str__(self) -> str:
        status = "✓" if self.completed else " "
        return (
            f"[{status}] {self.time}  {self.description} "
            f"({self.duration_minutes} min) [{self.priority}]"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet that owns a list of care tasks."""

    name: str
    species: str = "dog"
    tasks: list[Task] = field(default_factory=list)
    id: int = field(default_factory=_next_id)

    def add_task(self, task: Task) -> Task:
        """Attach a task to this pet (stamping its name) and return it."""
        task.pet_name = self.name
        self.tasks.append(task)
        return task

    def remove_task(self, task: Task) -> None:
        """Detach a task from this pet if present."""
        if task in self.tasks:
            self.tasks.remove(task)

    def task_count(self) -> int:
        """Return how many tasks this pet currently has."""
        return len(self.tasks)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """A pet owner who manages one or more pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> Pet:
        """Register a pet under this owner and return it."""
        self.pets.append(pet)
        return pet

    def get_pet(self, name: str) -> "Pet | None":
        """Return the first pet matching name (case-insensitive), or None."""
        return next((p for p in self.pets if p.name.lower() == name.lower()), None)

    def all_tasks(self) -> list[Task]:
        """Return a flat list of every task across all of the owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


# ---------------------------------------------------------------------------
# Scheduler — the "brain"
# ---------------------------------------------------------------------------

@dataclass
class Scheduler:
    """Retrieves, organizes, and analyzes tasks across an owner's pets."""

    owner: Owner

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks ordered chronologically by their HH:MM time."""
        tasks = self.owner.all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: t.minutes_since_midnight)

    def sort_by_priority(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks ordered by priority (high first), then by time."""
        tasks = self.owner.all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: (t.priority_rank, t.minutes_since_midnight))

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return only the tasks belonging to the named pet."""
        return [t for t in self.owner.all_tasks() if t.pet_name.lower() == pet_name.lower()]

    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return tasks matching the given completion status."""
        return [t for t in self.owner.all_tasks() if t.completed == completed]

    def todays_schedule(self) -> list[Task]:
        """Return today's pending tasks sorted by time (the daily plan)."""
        today = date.today().isoformat()
        pending = [t for t in self.owner.all_tasks() if not t.completed and t.due_date == today]
        return self.sort_by_time(pending)

    def detect_conflicts(self) -> list[str]:
        """Return warning strings for any pending tasks sharing a time slot."""
        warnings: list[str] = []
        by_time: dict[str, list[Task]] = {}
        for task in self.owner.all_tasks():
            if task.completed:
                continue
            by_time.setdefault(task.time, []).append(task)
        for time_slot, tasks in sorted(by_time.items()):
            if len(tasks) > 1:
                labels = ", ".join(f"{t.description} ({t.pet_name})" for t in tasks)
                warnings.append(f"⚠️ Conflict at {time_slot}: {labels}")
        return warnings

    def complete_task(self, task: Task) -> "Task | None":
        """Mark a task complete; re-attach its next occurrence to the same pet."""
        next_task = task.mark_complete()
        if next_task is not None:
            pet = self.owner.get_pet(task.pet_name)
            if pet is not None:
                pet.add_task(next_task)
        return next_task

    def explain_plan(self) -> str:
        """Return a human-readable daily plan with any conflict warnings."""
        lines = [f"Daily plan for {self.owner.name}'s pets:"]
        schedule = self.todays_schedule()
        if not schedule:
            lines.append("  (no pending tasks today)")
        for task in schedule:
            lines.append(f"  {task.time} — {task.description} "
                         f"({task.duration_minutes} min) "
                         f"[priority: {task.priority}] for {task.pet_name}")
        for warning in self.detect_conflicts():
            lines.append("  " + warning)
        return "\n".join(lines)

    # -- Stretch: persistence -------------------------------------------------

    def save_to_json(self, path: str) -> None:
        """Serialize the owner, pets, and tasks to a JSON file."""
        data = {
            "owner": self.owner.name,
            "pets": [
                {
                    "name": pet.name,
                    "species": pet.species,
                    "tasks": [asdict(t) for t in pet.tasks],
                }
                for pet in self.owner.pets
            ],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    @staticmethod
    def load_from_json(path: str) -> "Scheduler":
        """Rebuild a Scheduler (owner/pets/tasks) from a JSON file."""
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        owner = Owner(name=data["owner"])
        for pet_data in data["pets"]:
            pet = Pet(name=pet_data["name"], species=pet_data["species"])
            for t in pet_data["tasks"]:
                t.pop("id", None)
                t.pop("pet_name", None)
                pet.add_task(Task(**t))
            owner.add_pet(pet)
        return Scheduler(owner=owner)
