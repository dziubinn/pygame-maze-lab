import time
from typing import Callable, Generator, Any

# --- 4. Декоратори ---
def debug_trace(func: Callable) -> Callable:
    """Декоратор, який виводить повідомлення про виклик функції."""
    def wrapper(*args, **kwargs):
        # print(f"[TRACE] Виклик {func.__name__}") # Можна розкоментувати для дебагу
        return func(*args, **kwargs)
    return wrapper

# --- 3. Лексичне замикання ---
def make_score_adder(bonus: int) -> Callable[[int], int]:
    """Замикання: створює функцію, яка додає фіксований бонус до очок."""
    def adder(current_score: int) -> int:
        return current_score + bonus
    return adder

# --- 2. Генератори ---
def id_generator(start: int = 0) -> Generator[int, None, None]:
    """Генератор унікальних ID для об'єктів."""
    current = start
    while True:
        yield current
        current += 1