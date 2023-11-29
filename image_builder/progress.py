import time
from typing import List


class Status:
    name: str
    emoji: str

    def __str__(self):
        return f"{self.name.capitalize()} {self.emoji}"


class PendingStatus(Status):
    name = "pending"
    emoji = ":large_blue_circle:"


class RunningStatus(Status):
    name = "running"
    emoji = ":hourglass_flowing_sand:"


class SuccessStatus(Status):
    name = "success"
    emoji = ":large_green_circle:"


class FailureStatus(Status):
    name = "failure"
    emoji = ":red_circle:"


class Phase:
    name: str
    description: str
    status: Status
    start_time: float
    end_time: float

    def __init__(self, name):
        self.name = name
        self.status = PendingStatus()

    def __str__(self):
        output = f"*{self.name.capitalize()}*: {self.status}"
        if self.status.name == "failure" or self.status.name == "success":
            output += f" ({round(self.end_time - self.start_time)} s)"
        return output

    def set_status(self, status: Status):
        self.status = status
        if status.name == "running":
            self.start_time = time.time()
        else:
            self.end_time = time.time()


class Progress:
    phases: List[Phase]
    phase: int

    def __init__(self):
        self.phases = [
            Phase("setup"),
            Phase("build"),
            Phase("publish"),
        ]
        self.phase = 0

    def set_current_phase(self, phase_name: str):
        for index, phase in enumerate(self.phases):
            if phase.name == phase_name:
                self.phase = index

    def get_phase(self, phase_name: str):
        for index, phase in enumerate(self.phases):
            if phase.name == phase_name:
                return phase

    def current_phase_running(self):
        self.phases[self.phase].set_status(RunningStatus())

    def current_phase_failure(self):
        self.phases[self.phase].set_status(FailureStatus())

    def current_phase_success(self):
        self.phases[self.phase].set_status(SuccessStatus())
