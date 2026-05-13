#!/usr/bin/env python3
import os
import pandas as pd
from datetime import datetime, timedelta
import textwrap
import math

# FIXED SAVE LOCATION
CSV_PATH_DEFAULT = "C:/Users/gatra/Downloads/task tracker/Task_Tracker_Dataset.csv"

DATE_FMT = "%Y-%m-%d"
TS_FMT = "%Y-%m-%dT%H:%M:%S"

PRIORITIES = ["Low", "Medium", "High", "Critical"]
STATUSES = ["To-Do", "In Progress", "Completed", "Overdue"]


def now_ts():
    return datetime.now().strftime(TS_FMT)


def parse_date(s):
    if not s or pd.isna(s):
        return None
    try:
        return datetime.strptime(s, DATE_FMT)
    except:
        return None


def ensure_df_columns(df):
    cols = [
        "task_id","title","description","project_id","category","assignee","created_at",
        "start_date","due_date","priority","status","estimated_time_hours","time_spent_hours",
        "subtasks","recurrence","reminder_datetime","tags","dependencies","comments_count",
        "completed_at","difficulty_level","actual_duration_hours"
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]


def load_tasks(path=CSV_PATH_DEFAULT):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
        df = ensure_df_columns(df)
        print(f"\nLoaded {len(df)} tasks from:\n{path}\n")
        return df
    else:
        print("\nNo existing dataset found. Starting new.\n")
        return pd.DataFrame(columns=ensure_df_columns(pd.DataFrame()).columns)



def save_tasks(df):
    df.to_csv(CSV_PATH_DEFAULT, index=False)
    print(f"\n💾 Saved {len(df)} tasks to:\n{CSV_PATH_DEFAULT}\n")


# AUTO-INCREMENT SEQUENTIAL TASK ID
def generate_task_id(df):
    if df.empty:
        next_id = 1
    else:
        numeric_ids = pd.to_numeric(df["task_id"], errors="coerce")
        next_id = numeric_ids.max() + 1
    print(f"\nAssigned Task ID: {int(next_id)}")
    return str(int(next_id))


def input_date(prompt):
    while True:
        s = input(prompt + " (YYYY-MM-DD or blank): ").strip()
        if s == "":
            return ""
        if parse_date(s):
            return s
        print("Invalid date format. Try again.")


# CASE-INSENSITIVE PRIORITY/STATUS INPUT
def choose_from(prompt, options, allow_blank=False):
    options_lower = [opt.lower() for opt in options]
    while True:
        v = input(f"{prompt} {options}: ").strip()
        if allow_blank and v == "":
            return ""
        if v.lower() in options_lower:
            return options[options_lower.index(v.lower())]
        print("Invalid choice. Try again.")


# ADD TASK
def add_task(df):
    print("\n=== ADD TASK ===")

    task_id = generate_task_id(df)

    task = {
        "task_id": task_id,
        "title": input("Title: ").strip(),
        "description": input("Description: ").strip(),
        "project_id": input("Project ID: ").strip(),
        "category": input("Category: ").strip(),
        "assignee": input("Assignee: ").strip(),
        "created_at": now_ts(),
        "start_date": input_date("Start date"),
        "due_date": input_date("Due date"),
        "priority": choose_from("Priority", PRIORITIES, allow_blank=True) or "Medium",
        "status": choose_from("Status", STATUSES, allow_blank=True) or "To-Do",
        "estimated_time_hours": 0.0,
        "time_spent_hours": 0.0,
        "subtasks": "[]",
        "recurrence": "",
        "reminder_datetime": "",
        "tags": input("Tags: ").strip(),
        "dependencies": "",
        "comments_count": 0,
        "completed_at": "",
        "difficulty_level": "",
        "actual_duration_hours": 0.0
    }

    df = df._append(task, ignore_index=True)
    print(f"\n✔ Task Added Successfully — ID: {task_id}")
    save_tasks(df)
    return df


# EDIT TASK
def edit_task(df):
    key = input("Enter Task ID or Title to edit: ").strip()
    row = df[(df["task_id"] == key) | (df["title"].str.contains(key, case=False, na=False))]

    if row.empty:
        print("❌ Task not found")
        return df

    idx = row.index[0]
    print("\nLeave blank to keep previous value.\n")

    for field in ["title","description","project_id","category","assignee","start_date","due_date","priority","status","tags"]:
        old = df.at[idx, field]
        new = input(f"{field} [{old}]: ").strip()
        if new:
            df.at[idx, field] = new

    save_tasks(df)
    print("✔ Task edited" \
    " successfully")
    return df


def delete_task(df):
    key = input("Enter Task ID or Title to delete: ").strip()

    # Try exact task ID match first
    row = df[df["task_id"].astype(str) == key]

    # If still not found, try title contains
    if row.empty:
        row = df[df["title"].str.contains(key, case=False, na=False)]

    if row.empty:
        print("❌ Task not found")
        return df

    idx = row.index[0]
    title = df.at[idx, "title"]

    confirm = input(f"Are you sure you want to delete '{title}'? (y/n): ").lower()
    if confirm == "y":
        df = df.drop(index=idx).reset_index(drop=True)
        df["task_id"] = [str(i) for i in range(1, len(df) + 1)]
        save_tasks(df)
        print("✔ Task deleted and IDs rearranged")
    else:
        print("❌ Delete cancelled")

    return df

# UPDATE STATUS
def update_status(df):
    key = input("Enter Task ID or Title: ").strip()
    row = df[(df['task_id'] == key) | (df['title'].str.contains(key, case=False))]

    if row.empty:
        print("❌ Task not found.")
        return df

    idx = row.index[0]
    df.at[idx, "status"] = choose_from("New Status", STATUSES)
    print("✔ Status Updated")

    if df.at[idx, "status"] == "Completed":
        df.at[idx, "completed_at"] = now_ts()

    save_tasks(df)
    return df


# SEARCH
def simple_search(df):
    q = input("Search keyword: ").strip()
    hits = df[
        df["title"].str.contains(q, case=False, na=False) |
        df["description"].str.contains(q, case=False, na=False) |
        df["tags"].str.contains(q, case=False, na=False)
    ]
    print(hits[['task_id','title','assignee','status','priority','due_date','tags']].to_string(index=False)
          if not hits.empty else "\nNo matching tasks.")


# ANALYTICS
def analytics(df):
    total = len(df)
    completed = len(df[df["status"] == "Completed"])
    print("\n=== ANALYTICS ===")
    print(f"Total tasks: {total}")
    print(f"Completed: {completed}")
    print(f"Completion Rate: {(completed/total*100):.1f}%" if total else "0%")

    today = datetime.now().date()

    def overdue(row):
        d = parse_date(row["due_date"])
        return d and d.date() < today and row["status"] != "Completed"

    df["overdue"] = df.apply(overdue, axis=1).fillna(False)

    overdue_tasks = df[df["overdue"] == True]

    print("\nOverdue Tasks:")
    if not overdue_tasks.empty:
        print(overdue_tasks[['task_id','title','assignee','due_date','priority']].to_string(index=False))
    else:
        print("No overdue tasks.")



# EXPORT VIEW
def export_filtered_view(df):
    tag = input("Filter Tag: ").strip()
    df2 = df[df["tags"].fillna("").str.contains(tag, case=False)] if tag else df
    df2.to_csv("exported_tasks.csv", index=False)
    print("\n✔ Exported to exported_tasks.csv")



def list_tasks(df):
    print(df[['task_id','title','assignee','status','priority','due_date','tags']].to_string(index=False)
          if not df.empty else "\nNo tasks available.")


# MAIN MENU
def main():
    df = load_tasks()

    while True:
        print(textwrap.dedent("""
        ===== TASK TRACKER =====
        1) Add Task
        2) Edit Task
        3) Delete Task
        4) Update Task Status
        5) Search Task
        6) Analytics
        7) List Tasks
        8) Export Filtered CSV
        9) Load Tasks
        0) Exit
        """))

        choice = input("Choose: ").strip()

        if choice == "1": df = add_task(df)
        elif choice == "2": df = edit_task(df)
        elif choice == "3": df = delete_task(df)
        elif choice == "4": df = update_status(df)
        elif choice == "5": simple_search(df)
        elif choice == "6": analytics(df)
        elif choice == "7": list_tasks(df)
        elif choice == "8": export_filtered_view(df)
        elif choice == "9": df = load_tasks()
        elif choice == "0":
            save_tasks(df)
            print("Goodbye!")
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()