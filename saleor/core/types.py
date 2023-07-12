class EventTypeBase:
    _event_type_names = set()
    CHOICES: list[tuple[str, str]] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for event_name, _ in cls.CHOICES:
            if event_name in cls._event_type_names:
                raise RuntimeError(
                    f"{cls.__name__} type {event_name!r} is not globally unique."
                )
            cls._event_type_names.add(event_name)
