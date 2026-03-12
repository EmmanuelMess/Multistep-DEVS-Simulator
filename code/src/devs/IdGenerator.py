from typing import Dict

from src.devs.Types import Id

usedIds: Dict[str, int] = {}
def generateId(name: str) -> Id:
    if name not in usedIds.keys():
        usedIds[name] = 0

    usedIds[name] += 1

    return f"<{name}:{usedIds[name]}>"