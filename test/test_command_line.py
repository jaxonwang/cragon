import pytest

from cragon import command_line


def test_time_parse():
    assert float(11) == command_line.parse_time("11")
    assert float(121) == command_line.parse_time("121")
    assert float(1821) == command_line.parse_time("30:21")
    assert float(12*3600+1821) == command_line.parse_time("12:30:21")
    with pytest.raises(ValueError):
        command_line.parse_time("1:3:3:3")
    with pytest.raises(ValueError):
        command_line.parse_time("2:34f:j")
    with pytest.raises(ValueError):
        command_line.parse_time("fdasj")
