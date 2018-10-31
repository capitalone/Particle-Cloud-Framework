from enum import Enum

State = Enum("State", "running stopped terminated pending")

STATE_STRING_TO_ENUM = {
    "State.running": State.running,
    "State.stopped": State.stopped,
    "State.terminated": State.terminated,
    "running": State.running,
    "stopped": State.stopped,
    "terminated": State.terminated
}
