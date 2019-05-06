from enum import Enum

State = Enum("State", "running stopped terminated pending")

STATE_STRING_TO_ENUM = dict([(s.name, s) for s in State]+[(str(s), s) for s in State])
