"""
Tests para alerts.py
Usamos un archivo SQLite temporal para cada test, así no tocamos la base real.
"""
import os
import tempfile

import pytest

from alerts import (
    init_db,
    add_alert,
    list_alerts,
    get_all_active_alerts,
    deactivate_alert,
    alert_is_triggered,
    Alert,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    os.remove(path)


def test_add_and_list_alert(temp_db):
    alert_id = add_alert(chat_id=123, asset="blue", operator="<", target_value=1200, db_path=temp_db)

    alerts = list_alerts(chat_id=123, db_path=temp_db)

    assert len(alerts) == 1
    assert alerts[0].id == alert_id
    assert alerts[0].asset == "blue"
    assert alerts[0].operator == "<"
    assert alerts[0].target_value == 1200


def test_invalid_operator_raises(temp_db):
    with pytest.raises(ValueError):
        add_alert(chat_id=123, asset="blue", operator="=", target_value=1200, db_path=temp_db)


def test_deactivate_alert_removes_from_active_list(temp_db):
    alert_id = add_alert(chat_id=123, asset="blue", operator="<", target_value=1200, db_path=temp_db)

    deactivate_alert(alert_id, db_path=temp_db)
    alerts = list_alerts(chat_id=123, db_path=temp_db)

    assert len(alerts) == 0


def test_get_all_active_alerts_across_users(temp_db):
    add_alert(chat_id=1, asset="blue", operator="<", target_value=1200, db_path=temp_db)
    add_alert(chat_id=2, asset="bitcoin", operator=">", target_value=60000, db_path=temp_db)

    all_alerts = get_all_active_alerts(db_path=temp_db)

    assert len(all_alerts) == 2


@pytest.mark.parametrize(
    "operator,target,current,expected",
    [
        ("<", 1200, 1100, True),
        ("<", 1200, 1300, False),
        (">", 60000, 65000, True),
        (">", 60000, 55000, False),
    ],
)
def test_alert_is_triggered(operator, target, current, expected):
    alert = Alert(id=1, chat_id=123, asset="test", operator=operator, target_value=target, active=True)
    assert alert_is_triggered(alert, current) == expected
