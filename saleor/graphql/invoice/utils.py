def is_event_active_for_any_plugin(event: str, plugins_list):
    return any(
        [plugin.is_event_active(event) for plugin in plugins_list if plugin.active]
    )
