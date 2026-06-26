"""Automated tests for the PawPal+ logic layer."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Task, Scheduler


@pytest.fixture
def scheduler() -> Scheduler:
    """A scheduler with one owner, two pets, and a few out-of-order tasks."""
    owner = Owner(name="Jordan")
    mochi = owner.add_pet(Pet(name="Mochi", species="dog"))
    biscuit = owner.add_pet(Pet(name="Biscuit", species="cat"))
    mochi.add_task(Task("Evening walk", time="18:30", priority="high"))
    mochi.add_task(Task("Morning walk", time="08:00", priority="high", frequency="daily"))
    biscuit.add_task(Task("Lunch", time="12:00", priority="low"))
    return Scheduler(owner=owner)


# -- Core behaviors ----------------------------------------------------------

def test_mark_complete_changes_status():
    """mark_complete() flips a task's completed flag to True."""
    task = Task("Walk", time="09:00")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_count():
    """Adding a task to a pet increments that pet's task count."""
    pet = Pet(name="Rex")
    assert pet.task_count() == 0
    pet.add_task(Task("Feed", time="07:00"))
    assert pet.task_count() == 1


def test_owner_all_tasks_aggregates_across_pets(scheduler):
    """Owner.all_tasks() returns tasks from every pet."""
    assert len(scheduler.owner.all_tasks()) == 3


# -- Sorting -----------------------------------------------------------------

def test_sort_by_time_is_chronological(scheduler):
    """sort_by_time() returns tasks in ascending HH:MM order."""
    times = [t.time for t in scheduler.sort_by_time()]
    assert times == ["08:00", "12:00", "18:30"]


def test_sort_by_priority_high_first(scheduler):
    """sort_by_priority() puts high-priority tasks before low ones."""
    priorities = [t.priority for t in scheduler.sort_by_priority()]
    assert priorities == ["high", "high", "low"]


# -- Filtering ---------------------------------------------------------------

def test_filter_by_pet(scheduler):
    """filter_by_pet() returns only the named pet's tasks."""
    mochi_tasks = scheduler.filter_by_pet("Mochi")
    assert len(mochi_tasks) == 2
    assert all(t.pet_name == "Mochi" for t in mochi_tasks)


def test_filter_by_status(scheduler):
    """filter_by_status() splits tasks by completion flag."""
    assert len(scheduler.filter_by_status(completed=False)) == 3
    scheduler.owner.all_tasks()[0].mark_complete()
    assert len(scheduler.filter_by_status(completed=True)) == 1


# -- Recurrence --------------------------------------------------------------

def test_daily_recurrence_creates_next_day_task():
    """Completing a daily task creates a new task due the following day."""
    today = date.today()
    task = Task("Walk", time="08:00", frequency="daily", due_date=today.isoformat())
    nxt = task.mark_complete()
    assert nxt is not None
    assert nxt.completed is False
    assert nxt.due_date == (today + timedelta(days=1)).isoformat()


def test_weekly_recurrence_creates_next_week_task():
    """Completing a weekly task schedules the next one seven days later."""
    today = date.today()
    task = Task("Bath", time="10:00", frequency="weekly", due_date=today.isoformat())
    nxt = task.mark_complete()
    assert nxt.due_date == (today + timedelta(days=7)).isoformat()


def test_once_task_does_not_recur():
    """A one-off task returns no follow-up when completed."""
    task = Task("Vet", time="14:00", frequency="once")
    assert task.mark_complete() is None


def test_scheduler_reattaches_recurring_task(scheduler):
    """complete_task() adds the next occurrence back onto the pet."""
    morning = next(t for t in scheduler.filter_by_pet("Mochi") if t.description == "Morning walk")
    before = scheduler.owner.get_pet("Mochi").task_count()
    scheduler.complete_task(morning)
    assert scheduler.owner.get_pet("Mochi").task_count() == before + 1


# -- Conflict detection ------------------------------------------------------

def test_detect_conflicts_flags_same_time():
    """Two pending tasks at the same time produce a conflict warning."""
    owner = Owner(name="Sam")
    pet = owner.add_pet(Pet(name="Fido"))
    pet.add_task(Task("Walk", time="08:00"))
    pet.add_task(Task("Feed", time="08:00"))
    warnings = Scheduler(owner=owner).detect_conflicts()
    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_no_conflict_when_times_differ(scheduler):
    """Distinct time slots yield no conflict warnings."""
    assert scheduler.detect_conflicts() == []


# -- Validation / edge cases -------------------------------------------------

def test_invalid_time_raises():
    """Constructing a Task with a bad time string raises ValueError."""
    with pytest.raises(ValueError):
        Task("Walk", time="25:99")


def test_invalid_priority_raises():
    """Constructing a Task with an unknown priority raises ValueError."""
    with pytest.raises(ValueError):
        Task("Walk", priority="urgent")


def test_pet_with_no_tasks_has_empty_schedule():
    """An owner whose pet has no tasks gets an empty daily schedule."""
    owner = Owner(name="Lee")
    owner.add_pet(Pet(name="Ghost"))
    assert Scheduler(owner=owner).todays_schedule() == []


# -- Persistence (stretch) ---------------------------------------------------

def test_save_and_load_roundtrip(tmp_path, scheduler):
    """Saving then loading reproduces the same task descriptions."""
    path = tmp_path / "data.json"
    scheduler.save_to_json(str(path))
    restored = Scheduler.load_from_json(str(path))
    original = {t.description for t in scheduler.owner.all_tasks()}
    assert {t.description for t in restored.owner.all_tasks()} == original
