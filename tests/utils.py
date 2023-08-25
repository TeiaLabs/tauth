from datetime import datetime


def validate_id(key, obj: dict):
    assert key in obj
    assert isinstance(obj[key], str)
    # TODO: assert encoding and hash


def validate_float(key, obj: dict):
    assert key in obj
    assert isinstance(obj[key], float)


def validate_int(key, obj: dict):
    assert key in obj
    assert isinstance(obj[key], int)


def validate_nonzero_int(key: str, obj: dict):
    validate_int(key, obj)
    assert key in obj
    assert isinstance(obj[key], int)
    assert obj[key] > 0


def validate_nonzero(key: str, obj: dict):
    assert key in obj
    assert obj[key] > 0


def validate_nonzero_float(key: str, obj: dict):
    assert key in obj
    assert isinstance(obj[key], float)
    assert obj[key] > 0


def validate_isostring(key: str, obj: dict):
    assert key in obj
    assert isinstance(obj[key], str)
    dt = datetime.fromisoformat(obj[key])
    assert isinstance(dt, datetime)


def run_validations(obj: dict, validations: dict) -> None:
    print(obj)
    print(type(validations))
    print(validations)
    print()
    for key, validation in validations.items():
        if isinstance(obj[key], list) and callable(validation):
            for item in obj[key]:
                run_validations(item, validation)
            continue
        elif isinstance(obj[key], list) and isinstance(validation, list):
            assert len(obj[key]) == len(validation)
            for item, val_item in zip(obj[key], validation):
                run_validations(item, val_item)
            continue
        if isinstance(obj[key], dict):
            run_validations(obj[key], validation)
            continue
        if callable(validation):
            validation(key, obj)
        else:
            print(key, obj[key], validation, sep="\n\n")
            assert obj[key] == validation


def validate_token(key, obj):
    value = obj[key]
    assert isinstance(value, str)
    assert value.startswith("MELT_")
    pieces = value.split("--")
    assert len(pieces) == 3
    assert len(pieces[-1]) >= 16


def validate_nonempty_string(key, obj):
    assert key in obj
    assert isinstance(obj[key], str)
    assert len(obj[key]) > 0


def validate_chatml_role(key, obj):
    assert key in obj
    assert isinstance(obj[key], str)
    assert obj[key] in {"system", "user", "assistant"}
