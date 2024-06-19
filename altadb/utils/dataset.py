import random
import time
import string


def random_word() -> str:
    return "".join(
        random.choice(string.ascii_lowercase) for i in range(random.randint(5, 10))
    )


def generate_import_label() -> str:
    return f"CLI - {random_word()} - {random_word()} - {random_word()} - {random_word()} - {time.time_ns()}"


__all__ = [
    "generate_import_label",
]
