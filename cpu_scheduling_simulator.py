
import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Each process: PID, Arrival Time, Burst Time, Priority
def fcfs(processes):
    return non_preemptive(processes, "FCFS")


def sjf(processes):
    return non_preemptive(processes, "SJF")


def priority_scheduling(processes):
    return non_preemptive(processes, "Priority")


def non_preemptive(processes, algorithm):
    remaining = [p.copy() for p in processes]
    time = 0
    completed = {}
    gantt = []

    while remaining:
        ready = [p for p in remaining if p["arrival"] <= time]

        if not ready:
            next_time = min(p["arrival"] for p in remaining)
            gantt.append(("Idle", time, next_time))
            time = next_time
            continue

        if algorithm == "FCFS":
            p = min(ready, key=lambda x: (x["arrival"], x["pid"]))
        elif algorithm == "SJF":
            p = min(ready, key=lambda x: (
                x["burst"], x["arrival"], x["pid"]))
        else:
            # Lower number means higher priority
            p = min(ready, key=lambda x: (
                x["priority"], x["arrival"], x["pid"]))

        start = time
        time += p["burst"]
        completed[p["pid"]] = time
        gantt.append((p["pid"], start, time))
        remaining.remove(p)

    return completed, gantt


def round_robin(processes, quantum):
    ordered = sorted(processes, key=lambda x: (x["arrival"], x["pid"]))
    queue = deque()
    remaining = {p["pid"]: p["burst"] for p in ordered}
    completed = {}
    gantt = []
    time = 0
    i = 0

    while i < len(ordered) or queue:
        if not queue and i < len(ordered):
            if time < ordered[i]["arrival"]:
                gantt.append(("Idle", time, ordered[i]["arrival"]))
                time = ordered[i]["arrival"]

        while i < len(ordered) and ordered[i]["arrival"] <= time:
            queue.append(ordered[i])
            i += 1

        if not queue:
            continue

        p = queue.popleft()
        start = time
        run_time = min(quantum, remaining[p["pid"]])
        time += run_time
        remaining[p["pid"]] -= run_time
        gantt.append((p["pid"], start, time))

        # Add processes that arrived while this process was running
        while i < len(ordered) and ordered[i]["arrival"] <= time:
            queue.append(ordered[i])
            i += 1

        if remaining[p["pid"]] > 0:
            queue.append(p)
        else:
            completed[p["pid"]] = time

    return completed, gantt


def calculate_metrics(processes, completed):
    results = []

    for p in processes:
        ct = completed[p["pid"]]
        tat = ct - p["arrival"]
        wt = tat - p["burst"]

        results.append({
            "pid": p["pid"],
            "arrival": p["arrival"],
            "burst": p["burst"],
            "priority": p["priority"],
            "completion": ct,
            "turnaround": tat,
            "waiting": wt
        })

    avg_wait = sum(r["waiting"] for r in results) / len(results)
    avg_tat = sum(r["turnaround"] for r in results) / len(results)

    return results, avg_wait, avg_tat


# ---------------- GUI ----------------

class CPUSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Scheduling Simulator")
        self.root.geometry("1050x780")
        self.root.minsize(850, 650)

        title = tk.Label(
            root,
            text="CPU Scheduling Simulator",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=10)

        tk.Label(
            root,
            text="Enter one process per line: PID Arrival Burst Priority"
        ).pack()

        self.input_box = tk.Text(root, height=6, width=55, font=("Consolas", 11))
        self.input_box.pack(pady=5)

        self.input_box.insert(
            "1.0",
            "P1 0 5 2\nP2 1 3 1\nP3 2 1 3"
        )

        controls = tk.Frame(root)
        controls.pack(pady=8)

        tk.Label(controls, text="Algorithm:").grid(row=0, column=0, padx=5)

        self.algorithm = ttk.Combobox(
            controls,
            values=["FCFS", "SJF", "Priority", "Round Robin"],
            state="readonly",
            width=16
        )
        self.algorithm.current(0)
        self.algorithm.grid(row=0, column=1, padx=5)

        tk.Label(controls, text="Time Quantum:").grid(
            row=0, column=2, padx=5
        )

        self.quantum = tk.Entry(controls, width=6)
        self.quantum.insert(0, "2")
        self.quantum.grid(row=0, column=3, padx=5)

        tk.Button(
            controls,
            text="Run Simulation",
            command=self.run_simulation,
            bg="#1976D2",
            fg="white",
            font=("Arial", 10, "bold")
        ).grid(row=0, column=4, padx=10)

        tk.Button(
            controls,
            text="Compare All",
            command=self.compare_all
        ).grid(row=0, column=5, padx=5)

        columns = (
            "PID", "Arrival", "Burst", "Priority",
            "Completion", "Turnaround", "Waiting"
        )

        self.table = ttk.Treeview(
            root, columns=columns, show="headings", height=6
        )

        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=105, anchor="center")

        self.table.pack(fill="x", padx=12, pady=8)

        self.summary = tk.Label(
            root,
            text="Enter processes and click Run Simulation.",
            font=("Arial", 11, "bold")
        )
        self.summary.pack(pady=5)

        self.chart_frame = tk.Frame(root)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def read_processes(self):
        processes = []
        lines = self.input_box.get("1.0", "end").strip().splitlines()
        seen = set()

        if not lines:
            raise ValueError("Please enter at least one process.")

        for line in lines:
            parts = line.split()

            if len(parts) != 4:
                raise ValueError(
                    "Each line must contain: PID Arrival Burst Priority"
                )

            pid = parts[0]

            try:
                arrival, burst, priority = map(int, parts[1:])
            except ValueError:
                raise ValueError("Arrival, burst, and priority must be integers.")

            if pid in seen:
                raise ValueError("Process IDs must be unique.")

            if arrival < 0 or burst <= 0 or priority < 0:
                raise ValueError(
                    "Arrival and priority must be non-negative; "
                    "burst time must be positive."
                )

            seen.add(pid)
            processes.append({
                "pid": pid,
                "arrival": arrival,
                "burst": burst,
                "priority": priority
            })

        return processes

    def run_algorithm(self, processes, algorithm):
        if algorithm == "FCFS":
            return fcfs(processes)
        elif algorithm == "SJF":
            return sjf(processes)
        elif algorithm == "Priority":
            return priority_scheduling(processes)
        else:
            try:
                quantum = int(self.quantum.get())
            except ValueError:
                raise ValueError("Time quantum must be a positive integer.")

            if quantum <= 0:
                raise ValueError("Time quantum must be greater than zero.")

            return round_robin(processes, quantum)

    def draw_chart(self, gantt, algorithm):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(10, 2.5))
        colors = plt.get_cmap("tab20")

        for i, (pid, start, end) in enumerate(gantt):
            color = "#BDBDBD" if pid == "Idle" else colors(i % 20)
            ax.barh(
                0, end - start, left=start, height=0.5,
                color=color, edgecolor="black"
            )
            ax.text(
                (start + end) / 2, 0, pid,
                ha="center", va="center", fontsize=9
            )
            ax.text(start, -0.38, str(start), ha="center", fontsize=8)

        if gantt:
            ax.text(gantt[-1][2], -0.38, str(gantt[-1][2]),
                    ha="center", fontsize=8)

        ax.set_title(f"Gantt Chart - {algorithm}")
        ax.set_xlabel("CPU Time")
        ax.set_yticks([])
        ax.set_xlim(left=0)
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    def run_simulation(self):
        try:
            processes = self.read_processes()
            algorithm = self.algorithm.get()
            completed, gantt = self.run_algorithm(processes, algorithm)
            results, avg_wait, avg_tat = calculate_metrics(
                processes, completed
            )

            for item in self.table.get_children():
                self.table.delete(item)

            for r in results:
                self.table.insert("", "end", values=(
                    r["pid"], r["arrival"], r["burst"], r["priority"],
                    r["completion"], r["turnaround"], r["waiting"]
                ))

            self.summary.config(
                text=f"{algorithm} | Average Waiting Time: {avg_wait:.2f}"
                     f" | Average Turnaround Time: {avg_tat:.2f}"
            )
            self.draw_chart(gantt, algorithm)

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def compare_all(self):
        try:
            processes = self.read_processes()
            algorithms = ["FCFS", "SJF", "Priority", "Round Robin"]
            comparison = []

            for algorithm in algorithms:
                completed, _ = self.run_algorithm(processes, algorithm)
                _, avg_wait, avg_tat = calculate_metrics(
                    processes, completed
                )
                comparison.append(
                    (algorithm, avg_wait, avg_tat)
                )

            message = "Algorithm Performance Comparison\n\n"

            for name, wait, tat in comparison:
                message += (
                    f"{name}:\n"
                    f"  Average Waiting Time: {wait:.2f}\n"
                    f"  Average Turnaround Time: {tat:.2f}\n\n"
                )

            messagebox.showinfo("Comparison Results", message)

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = CPUSimulator(root)
    root.mainloop()
