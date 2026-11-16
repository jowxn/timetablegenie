from ortools.sat.python import cp_model
from synthetic_data import get_synthetic_data
import pandas as pd

def solve_timetable(data):
    model = cp_model.CpModel()
    
    days = data["days"]
    slots_per_day = data["slots_per_day"]
    total_slots = data["total_slots"]
    rooms = data["rooms"]
    faculty = data["faculty"]
    lunch_slot = data["lunch_slot_index"]
    
    instances = []
    for sess in data["sessions"]:
        for k in range(sess["weekly_sessions"]):
            instances.append({
                "inst_id": f"{sess['id']}_{k+1}",
                "course": sess["course"],
                "category": sess["category"],
                "batch": sess["batch"],
                "faculty": sess["faculty"],
                "room_type": sess["room_type"],
                "duration": sess["duration_slots"]
            })

    X = {}
    for i, inst in enumerate(instances):
        for s in range(total_slots):
            day_slot = s % slots_per_day
            
            if day_slot == lunch_slot:
                continue
            if inst["duration"] > 1:
                if day_slot + inst["duration"] > slots_per_day or (day_slot < lunch_slot and day_slot + inst["duration"] > lunch_slot):
                    continue

            for r, room in enumerate(rooms):
                if room["type"] == inst["room_type"]:
                    X[(i, s, r)] = model.NewBoolVar(f"x_{i}_{s}_{r}")

    # HARD CONSTRAINT 1: Every session instance scheduled once
    for i in range(len(instances)):
        model.Add(sum(X[(i, s, r)] for s in range(total_slots) for r in range(len(rooms)) if (i, s, r) in X) == 1)

    def get_occupying_vars(slot, filter_func):
        occupying = []
        for (i, s, r), var in X.items():
            dur = instances[i]["duration"]
            if s <= slot < s + dur and filter_func(i, r):
                occupying.append(var)
        return occupying

    # HARD CONSTRAINT 2: No Room Conflict
    for r in range(len(rooms)):
        for s in range(total_slots):
            model.Add(sum(get_occupying_vars(s, lambda i, room_idx: room_idx == r)) <= 1)

    # HARD CONSTRAINT 3: No Faculty Conflict
    for f in faculty:
        f_id = f["id"]
        for s in range(total_slots):
            model.Add(sum(get_occupying_vars(s, lambda i, r: instances[i]["faculty"] == f_id)) <= 1)

    # HARD CONSTRAINT 4: Batch / Student Cohort Conflict
    all_batches = set(inst["batch"] for inst in instances)
    for b in all_batches:
        for s in range(total_slots):
            model.Add(sum(get_occupying_vars(s, lambda i, r: instances[i]["batch"] == b)) <= 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = []
        for (i, s, r), var in X.items():
            if solver.Value(var) == 1:
                inst = instances[i]
                day_idx = s // slots_per_day
                slot_idx = s % slots_per_day
                schedule.append({
                    "Instance_ID": inst["inst_id"],
                    "Course": inst["course"],
                    "Category": inst["category"],
                    "Batch": inst["batch"],
                    "Faculty_ID": inst["faculty"],
                    "Room": rooms[r]["name"],
                    "Room_Type": rooms[r]["type"],
                    "Day": days[day_idx],
                    "Day_Idx": day_idx,
                    "Start_Slot": slot_idx,
                    "Duration": inst["duration"],
                    "Global_Start_Slot": s
                })
        return pd.DataFrame(schedule)
    else:
        return None
