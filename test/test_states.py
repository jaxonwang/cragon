import pytest
import time
import threading

from unittest import mock

from cragon import states


@pytest.fixture()
def reset():
    states.__current = states.State.INIT
    states.__callbacks = []


def test_callback(caplog):
    fake_callback1 = mock.Mock()
    fake_callback2 = mock.Mock()
    fake_callback3 = mock.Mock()
    states.add_callback(fake_callback1)
    states.add_callback(fake_callback2)
    states.add_callback(fake_callback3)

    states.setStartUp()
    fake_callback1.assert_called_once_with(
        states.State.INIT, states.State.STARTUP)
    fake_callback2.assert_called_once_with(
        states.State.INIT, states.State.STARTUP)
    fake_callback3.assert_called_once_with(
        states.State.INIT, states.State.STARTUP)

    assert len(caplog.records) == 1
    assert caplog.records[0].getMessage(
    ) == "The system's state changed from INIT to STARTUP."


def test_state_trans(reset):
    states.setStartUp()
    states.setProcessRunning()
    states.setCheckpointing()
    states.setProcessRunning()
    states.setCheckpointing()
    states.setProcessFinished()
    states.setTearDwon()


def test_transform(reset):
    with pytest.raises(AssertionError):
        states.__transform([], states.State.STARTUP)

    with pytest.raises(AssertionError):
        states.__transform([states.State.STARTUP], states.State.STARTUP)

    with pytest.raises(AssertionError):
        states.__transform(
            [states.State.STARTUP],
            states.State.PROCESS_RUNNING)

    states.__transform([states.State.INIT], states.State.STARTUP)
    assert states.get_current_state() == states.State.STARTUP
    states.__transform([states.State.STARTUP, states.State.PROCESS_RUNNING],
                       states.State.PROCESS_FINISHED)
    assert states.get_current_state() == states.State.PROCESS_FINISHED


def test_threadsafe(reset):
    fake_callback = mock.Mock()
    states.add_callback(fake_callback)

    def trans(to):
        time.sleep(0.00001)
        try:
            states.__transform([states.State.INIT], to)
        except AssertionError:
            pass

    s = [states.State.STARTUP,
         states.State.TEARDOWN,
         states.State.PROCESS_RUNNING,
         states.State.PROCESS_FINISHED,
         states.State.CHECKPOINTING
         ]
    for i in range(100):
        ths = [threading.Thread(target=trans, args=(i,)) for i in s]
        for t in ths:
            t.start()
        for t in ths:
            t.join()
        fake_callback.assert_called_once()
