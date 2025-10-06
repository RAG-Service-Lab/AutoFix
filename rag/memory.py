from langchain_core.chat_history import BaseChatMessageHistory

class InMemoryHistory(BaseChatMessageHistory): # 메시지 히스토리 관리
    def __init__(self):
        super().__init__()
        self.messages = []

    def add_messages(self, messages):
        self.messages.extend(messages)

    def clear(self):
        self.messages = []

    def __repr__(self):
        return str(self.messages)


def get_by_session_id(session_id, history): # 메시지 히스토리 주체 관리
    if session_id not in history:
        history[session_id] = InMemoryHistory()
    return history[session_id]