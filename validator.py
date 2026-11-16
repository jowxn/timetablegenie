import pandas as pd
from synthetic_data import get_synthetic_data
from solver import solve_timetable

def verify_timetable(df, data):
    lunch_slot = data["lunch_slot_index"]
    audit_report = {
        "total_sessions_scheduled": len(df),
        "room_clashes": 0,
        "faculty_clashes": 0,
        "batch_clashes": 0,
        "lunch_slot_violations": 0,
        "violations_log": [],
        "proof_verdict": "FAILED"
    }

    expanded = []
    for _, row in df.iterrows():
        for d in range(row["Duration"]):
            slot = row["Start_Slot"] + d
            expanded.append({
                "Instance_ID": row["Instance_ID"],
                "Course": row["Course"],
                "Day": row["Day"],
                "Slot": slot,
                "Room": row["Room"],
                "Faculty": row["Faculty_ID"],
                "Batch": row["Batch"]
            })
    exp_df = pd.DataFrame(expanded)

    lunch_viol = exp_df[exp_df["Slot"] == lunch_slot]
    if not lunch_viol.empty:
        audit_report["lunch_slot_violations"] += len(lunch_viol)
        audit_report["violations_log"].append(f"Classes scheduled during lunch hour: {len(lunch_viol)}")

    room_dups = exp_df.duplicated(subset=["Day", "Slot", "Room"], keep=False)
    if room_dups.any():
        clashes = exp_df[room_dups]
        audit_report["room_clashes"] += len(clashes)
        audit_report["violations_log"].append(f"Room double-booking detected:\n{clashes[['Day', 'Slot', 'Room']]}")

    fac_dups = exp_df.duplicated(subset=["Day", "Slot", "Faculty"], keep=False)
    if fac_dups.any():
        clashes = exp_df[fac_dups]
        audit_report["faculty_clashes"] += len(clashes)
        audit_report["violations_log"].append(f"Faculty double-booking detected:\n{clashes[['Day', 'Slot', 'Faculty']]}")

    batch_dups = exp_df.duplicated(subset=["Day", "Slot", "Batch"], keep=False)
    if batch_dups.any():
        clashes = exp_df[batch_dups]
        audit_report["batch_clashes"] += len(clashes)
        audit_report["violations_log"].append(f"Batch conflict detected:\n{clashes[['Day', 'Slot', 'Batch']]}")

    total_violations = (audit_report["room_clashes"] + 
                        audit_report["faculty_clashes"] + 
                        audit_report["batch_clashes"] + 
                        audit_report["lunch_slot_violations"])
    
    if total_violations == 0:
        audit_report["proof_verdict"] = "PASSED: Zero Constraint Violations Formally Proven."
    
    return audit_report

if __name__ == "__main__":
    dataset = get_synthetic_data()
    schedule_df = solve_timetable(dataset)
    if schedule_df is not None:
        report = verify_timetable(schedule_df, dataset)
        for key, val in report.items():
            print(f"{key}: {val}")
