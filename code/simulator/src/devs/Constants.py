from typing import Final

MAX_ITERATIONS: Final[int] = 1000
"""
After this amount of iterations the system breaks out to prevent infinite loops
"""

MAX_ATOMICS: Final[int] = 10000
"""
After this amount of `Atomics` the `AtomicGraph` crashes to prevent very large graphs
"""

MAX_PORTS: Final[int] = 100
"""
Maximum amount of ports allowed on Atomics
"""