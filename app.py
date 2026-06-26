"""PawPal+ Streamlit UI, wired to the pawpal_system logic layer."""

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A smart pet-care planner. Add pets and tasks, then build a daily plan.")

# --- Application memory -----------------------------------------------------
# Streamlit reruns top-to-bottom on every interaction, so the Owner must live
# in session_state to survive reruns instead of being re-created each time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner: Owner = st.session_state.owner
scheduler = Scheduler(owner=owner)

# --- Owner / pet setup ------------------------------------------------------
with st.sidebar:
    st.header("Owner")
    owner.name = st.text_input("Owner name", value=owner.name)

    st.header("Add a pet")
    with st.form("add_pet", clear_on_submit=True):
        pet_name = st.text_input("Pet name", value="Mochi")
        species = st.selectbox("Species", ["dog", "cat", "other"])
        if st.form_submit_button("Add pet") and pet_name:
            if owner.get_pet(pet_name):
                st.warning(f"{pet_name} already exists.")
            else:
                owner.add_pet(Pet(name=pet_name, species=species))
                st.success(f"Added {pet_name}.")

    st.header("Pets")
    if owner.pets:
        for pet in owner.pets:
            st.write(f"• {pet.name} ({pet.species}) — {pet.task_count()} tasks")
    else:
        st.info("No pets yet.")

# --- Add a task -------------------------------------------------------------
st.subheader("Add a task")
if not owner.pets:
    st.info("Add a pet in the sidebar first.")
else:
    with st.form("add_task", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            target_pet = st.selectbox("Pet", [p.name for p in owner.pets])
            description = st.text_input("Task", value="Morning walk")
            time_str = st.time_input("Time").strftime("%H:%M")
        with c2:
            duration = st.number_input("Duration (min)", 1, 240, 20)
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task") and description:
            owner.get_pet(target_pet).add_task(
                Task(description, time=time_str, duration_minutes=int(duration),
                     priority=priority, frequency=frequency)
            )
            st.success(f"Added '{description}' for {target_pet}.")

# --- Daily plan -------------------------------------------------------------
st.divider()
st.subheader("📋 Today's Plan")

col_a, col_b = st.columns(2)
sort_mode = col_a.radio("Sort by", ["time", "priority"], horizontal=True)
show_done = col_b.checkbox("Show completed", value=False)

tasks = owner.all_tasks()
if sort_mode == "time":
    tasks = scheduler.sort_by_time(tasks)
else:
    tasks = scheduler.sort_by_priority(tasks)
if not show_done:
    tasks = [t for t in tasks if not t.completed]

# Conflict warnings surfaced prominently for the owner.
for warning in scheduler.detect_conflicts():
    st.warning(warning)

if tasks:
    st.table(
        [
            {
                "Time": t.time,
                "Task": t.description,
                "Pet": t.pet_name,
                "Min": t.duration_minutes,
                "Priority": t.priority,
                "Freq": t.frequency,
                "Done": "✓" if t.completed else "",
            }
            for t in tasks
        ]
    )

    st.markdown("**Mark a task complete** (recurring tasks auto-reschedule):")
    pending = [t for t in owner.all_tasks() if not t.completed]
    if pending:
        labels = {f"{t.time} {t.description} ({t.pet_name})": t for t in pending}
        choice = st.selectbox("Task", list(labels))
        if st.button("Complete"):
            nxt = scheduler.complete_task(labels[choice])
            if nxt:
                st.success(f"Done! Next '{nxt.description}' scheduled for {nxt.due_date}.")
            else:
                st.success("Marked complete.")
            st.rerun()
else:
    st.info("No tasks to show. Add some above.")
