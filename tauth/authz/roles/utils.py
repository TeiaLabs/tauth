from typing import Annotated

from pydantic import AfterValidator


def check_unique_and_sort(input: list[str]) -> list[str]:
    input_as_set = set(input)
    if len(input) != len(input_as_set):
        raise ValueError("List contains duplicate values")
    return sorted(list(input_as_set))

UniqueOrderedList = Annotated[list[str], AfterValidator(check_unique_and_sort)]
