from enum import Enum, auto


class BotState(Enum):
    IDLE = auto()
    AWAITING_CATEGORY = auto()
    AWAITING_AMOUNT = auto()


class BotStateMachine:
    def __init__(self):
        self.state = BotState.IDLE
        self.context = {}

    def transition_to(self, new_state):
        self.state = new_state

    def get_state(self):
        return self.state

    def set_context(self, key, value):
        self.context[key] = value

    def get_context(self, key):
        return self.context.get(key)

    def clear_context(self):
        self.context.clear()
