
class BaseStrategy:
    def execute(self):
        pass

class DefaultStrategy(BaseStrategy):
    def execute(self):
        return "Default strategy executed"
