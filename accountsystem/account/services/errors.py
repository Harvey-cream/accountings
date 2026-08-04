"""AI 业务能力层可预期失败（由 Tool / 调用方处理，不含 HTTP）。"""


class ServiceError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
