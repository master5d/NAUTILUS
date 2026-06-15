import tray_logic


def _st(hosts=None, alerts=None):
    return {"hosts": hosts or {}, "alerts": alerts or []}


def test_color_green_when_all_live():
    state = _st({"m4": {"freshness": "live"}, "surface": {"freshness": "live"}})
    assert tray_logic.status_color(state) == "green"


def test_color_amber_when_any_stale():
    assert tray_logic.status_color(_st({"m4": {"freshness": "stale"}})) == "amber"


def test_color_red_when_any_down():
    assert tray_logic.status_color(_st({"m4": {"freshness": "down"}})) == "red"


def test_color_gray_when_no_hosts():
    assert tray_logic.status_color(_st()) == "gray"


def test_critical_alert_forces_red_even_if_live():
    state = _st({"m4": {"freshness": "live"}},
               [{"id": "x", "host": "m4", "severity": "critical"}])
    assert tray_logic.status_color(state) == "red"


def test_warning_alert_is_amber():
    state = _st({"m4": {"freshness": "live"}}, [{"severity": "warning"}])
    assert tray_logic.status_color(state) == "amber"


def test_alert_keys_and_new_alert_keys_diff():
    state = _st(alerts=[{"id": "a", "host": "m4"}, {"id": "b", "host": "m4"}])
    assert tray_logic.alert_keys(state) == {("a", "m4"), ("b", "m4")}
    assert tray_logic.new_alert_keys({("a", "m4")}, state) == {("b", "m4")}


def test_alert_keys_empty_state():
    assert tray_logic.alert_keys(_st()) == set()


def test_resolved_alert_does_not_drive_color():
    # a resolved critical lingering in the list must NOT redden the indicator
    state = _st({"m4": {"freshness": "live"}},
               [{"id": "x", "host": "m4", "severity": "critical", "state": "resolved"}])
    assert tray_logic.status_color(state) == "green"


def test_firing_alert_with_state_still_red():
    state = _st({"m4": {"freshness": "live"}},
               [{"id": "x", "host": "m4", "severity": "critical", "state": "firing"}])
    assert tray_logic.status_color(state) == "red"
