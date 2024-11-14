from ...utils.errors import EngineException


class PolicyNotFound(EngineException):
    pass


class RuleNotFound(EngineException):
    pass
