import os
import time
import pandas as pd
from google import genai
from google.genai import types

class TimetableAgent:
    def __init__(self, schedule_df, dataset, api_key: str = None):
        self.df = schedule_df
        self.data = dataset
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        self.time_labels = [
            "09:00 - 10:00",
            "10:00 - 11:00",
            "11:00 - 12:00",
            "12:00 - 01:00 (Lunch)",
            "01:00 - 02:00",
            "02:00 - 03:00"
        ]
        
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def run_agent_query(self, user_prompt: str) -> str:
        df = self.df
        data = self.data
        time_labels = self.time_labels

        def query_schedule(entity_type: str, entity_name: str, day: str = "") -> str:
            """
            Retrieves scheduled classes for a specific faculty member, student batch, or room.
            Args:
                entity_type: Must be 'faculty', 'batch', or 'room'.
                entity_name: Name or ID (e.g., 'F_ALICE', 'Alice', 'CSE_A', 'Lecture Hall 101').
                day: Optional day filter ('Mon', 'Tue', 'Wed', 'Thu', 'Fri').
            """
            sub = df.copy()
            if day:
                sub = sub[sub["Day"].str.lower() == day.lower().strip()]

            e_type = entity_type.lower().strip()
            name = entity_name.lower().strip()
            clean_name = name.replace("dr.", "").replace("prof.", "").strip()

            if "fac" in e_type:
                sub = sub[
                    sub["Faculty_ID"].str.lower().str.contains(clean_name) | 
                    sub["Course"].str.lower().str.contains(clean_name)
                ]
            elif "batch" in e_type or "class" in e_type:
                sub = sub[sub["Batch"].str.lower().str.contains(name)]
            elif "room" in e_type:
                sub = sub[sub["Room"].str.lower().str.contains(name)]
            else:
                return f"Unknown entity type: {entity_type}. Use 'faculty', 'batch', or 'room'."

            if sub.empty:
                return f"No sessions found for {entity_type} '{entity_name}'" + (f" on {day}." if day else ".")

            results = []
            for _, r in sub.iterrows():
                t_str = time_labels[r["Start_Slot"]]
                results.append(
                    f"- **{r['Day']}** at {t_str} ({r['Duration']} hr): {r['Course']} | Room: {r['Room']} | Batch: {r['Batch']} | Faculty: {r['Faculty_ID']}"
                )
            return "\n".join(results)

        def check_slot_availability(day: str, slot_number: int, room_name: str) -> str:
            """
            Checks if a particular classroom or lab is free at a specific slot number (0 to 5).
            Args:
                day: 'Mon', 'Tue', 'Wed', 'Thu', or 'Fri'.
                slot_number: Integer from 0 to 5.
                room_name: e.g. 'Lecture Hall 101', 'AI Systems Lab'.
            """
            if slot_number == data["lunch_slot_index"]:
                return f"Campus-wide policy: Slot {slot_number} (12:00 - 01:00) is reserved for Lunch Break."

            occupied = df[
                (df["Day"].str.lower() == day.lower().strip()) &
                (df["Start_Slot"] <= slot_number) &
                (df["Start_Slot"] + df["Duration"] > slot_number) &
                (df["Room"].str.lower().str.contains(room_name.lower().strip()))
            ]

            if occupied.empty:
                return f"{room_name} is **FREE** on {day} at Slot {slot_number} ({time_labels[slot_number]})."
            else:
                row = occupied.iloc[0]
                return f"{room_name} is **BUSY** on {day} at Slot {slot_number} ({row['Course']} with {row['Batch']})."

        def get_nep_policy_info(policy_topic: str) -> str:
            """
            Provides official guidelines regarding NEP-2020 timetable constraints.
            Args:
                policy_topic: 'lunch', 'lab', 'multidisciplinary', or 'general'.
            """
            topic = policy_topic.lower()
            if "lunch" in topic:
                return "NEP-L01: Slot 3 (12:00 - 13:00) is a mandatory, immovable lunch break across all departments."
            elif "lab" in topic:
                return "NEP-LAB: Practical/Lab sessions must occupy 2 continuous consecutive slots in dedicated laboratory facilities."
            elif "mde" in topic or "elective" in topic:
                return "NEP-MDE: Multidisciplinary electives permit cross-department student groups; classes must avoid clashes with core major lectures."
            return "NEP-General: Enforces zero teacher overlap, zero room double-booking, and room capacity limits."

        def local_fallback_router(prompt_text: str) -> str:
            p = prompt_text.lower()
            if "lunch" in p:
                return get_nep_policy_info("lunch")
            if "lab policy" in p or "lab rule" in p:
                return get_nep_policy_info("lab")

            target_day = ""
            for d in data["days"]:
                if d.lower() in p:
                    target_day = d
                    break

            for f in data["faculty"]:
                clean_f = f["name"].lower().replace("dr.", "").replace("prof.", "").split("(")[0].strip()
                if f["id"].lower() in p or clean_f in p:
                    return f"**Schedule for {f['name']} ({f['id']}):**\n" + query_schedule("faculty", f["id"], target_day)

            for b in data["batches"] + ["cse_a_elective_1", "cse_a_elective_2"]:
                if b.lower() in p:
                    return f"**Schedule for {b.upper()}:**\n" + query_schedule("batch", b, target_day)

            for r in data["rooms"]:
                if r["id"].lower() in p or r["name"].lower() in p:
                    return f"**Occupancy for {r['name']}:**\n" + query_schedule("room", r["name"], target_day)

            return (
                "Try asking about a specific teacher, batch, room, or policy:\n"
                "- *'What is Dr. Alice's schedule?'*\n"
                "- *'Show classes for CSE_B'*\n"
                "- *'Where is Lecture Hall 101 occupied?'*\n"
                "- *'Explain lunch break policy'*"
            )

        if self.client:
            system_instruction = (
                "You are the TimetableGenie AI Agent for CSC 473 (LLMs & Agentic AI). "
                "You have access to real-time tools to inspect the generated NEP-2020 timetable. "
                "Always call the appropriate tool when asked about schedules, room vacancies, or NEP rules. "
                "Note: Faculty IDs follow the format 'F_ALICE', 'F_BOB', 'F_CAROL', 'F_DAVID', 'F_EVE'. "
                "Provide concise, professional answers."
            )

            candidate_models = ["gemini-3.8-flash", "gemini-3.8-flash-lite"]
            for model_name in candidate_models:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            tools=[query_schedule, check_slot_availability, get_nep_policy_info],
                            temperature=0.2,
                        )
                    )
                    if response.text:
                        return f"*(Powered by {model_name})*\n\n" + response.text
                except Exception as e:
                    err = str(e)
                    if "503" in err or "UNAVAILABLE" in err or "429" in err or "404" in err:
                        continue
                    else:
                        return f"Agent Error: {err}"

        fallback_ans = local_fallback_router(user_prompt)
        return "*(Cloud LLM busy — resolved via Local Deterministic Tool Router)*\n\n" + fallback_ans
