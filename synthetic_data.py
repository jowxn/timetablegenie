import json

def get_synthetic_data():
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    slots_per_day = 6  # Slots: 0 (9-10), 1 (10-11), 2 (11-12), 3 (Lunch 12-1), 4 (1-2), 5 (2-3)
    
    rooms = [
        {"id": "LH_101", "name": "Lecture Hall 101", "capacity": 60, "type": "theory"},
        {"id": "LH_102", "name": "Lecture Hall 102", "capacity": 60, "type": "theory"},
        {"id": "LH_103", "name": "Lecture Hall 103", "capacity": 60, "type": "theory"},
        {"id": "LAB_1",  "name": "AI Systems Lab",   "capacity": 35, "type": "lab"},
        {"id": "LAB_2",  "name": "Hardware Lab",     "capacity": 35, "type": "lab"}
    ]
    
    faculty = [
        {"id": "F_ALICE", "name": "Dr. Alice (CSE)"},
        {"id": "F_BOB",   "name": "Prof. Bob (CSE)"},
        {"id": "F_CAROL", "name": "Dr. Carol (Math)"},
        {"id": "F_DAVID", "name": "Prof. David (Management)"},
        {"id": "F_EVE",   "name": "Dr. Eve (Design)"}
    ]

    batches = ["CSE_A", "CSE_B"]

    sessions = [
        # Batch CSE_A Core Major Courses
        {"id": "S1", "course": "Neural Networks", "category": "Major", "batch": "CSE_A", "faculty": "F_ALICE", "room_type": "theory", "duration_slots": 1, "weekly_sessions": 3},
        {"id": "S2", "course": "Discrete Mathematics", "category": "Major", "batch": "CSE_A", "faculty": "F_CAROL", "room_type": "theory", "duration_slots": 1, "weekly_sessions": 3},
        {"id": "S3", "course": "AI Programming Lab", "category": "Major Lab", "batch": "CSE_A", "faculty": "F_ALICE", "room_type": "lab", "duration_slots": 2, "weekly_sessions": 1},
        
        # Batch CSE_B Core Major Courses
        {"id": "S4", "course": "Database Systems", "category": "Major", "batch": "CSE_B", "faculty": "F_BOB", "room_type": "theory", "duration_slots": 1, "weekly_sessions": 3},
        {"id": "S5", "course": "Applied Statistics", "category": "Major", "batch": "CSE_B", "faculty": "F_CAROL", "room_type": "theory", "duration_slots": 1, "weekly_sessions": 3},
        {"id": "S6", "course": "Database Practicum", "category": "Major Lab", "batch": "CSE_B", "faculty": "F_BOB", "room_type": "lab", "duration_slots": 2, "weekly_sessions": 1},
        
        # NEP Multidisciplinary Elective (MDE)
        {"id": "S7", "course": "MDE: Tech Entrepreneurship", "category": "Elective", "batch": "CSE_A_ELECTIVE_1", "faculty": "F_DAVID", "room_type": "theory", "duration_slots": 1, "weekly_sessions": 2},
        {"id": "S8", "course": "MDE: UX & Product Design", "category": "Elective", "batch": "CSE_A_ELECTIVE_2", "faculty": "F_EVE", "room_type": "theory", "duration_slots": 1, "weekly_sessions": 2}
    ]

    return {
        "days": days,
        "slots_per_day": slots_per_day,
        "total_slots": len(days) * slots_per_day,
        "lunch_slot_index": 3,
        "rooms": rooms,
        "faculty": faculty,
        "batches": batches,
        "sessions": sessions
    }

if __name__ == "__main__":
    data = get_synthetic_data()
    print(f"Dataset generated: {len(data['sessions'])} session templates across {len(data['rooms'])} rooms.")
