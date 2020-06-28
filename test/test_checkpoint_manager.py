import pytest
import os

from pathlib import Path

from cragon import checkpoint_manager
from cragon import context

from . import general


@pytest.fixture(scope="function")
def set_context(tmpdir):
    stored_imagedir = context.ckpt_dir
    context.ckpt_dir = tmpdir

    yield

    context.ckpt_dir = stored_imagedir


@pytest.fixture(scope="function")
def mktestdirs(tmpdir, set_context):
    cwd = Path(tmpdir)
    cwd.joinpath("12_abc@cdef").touch()
    cwd.joinpath("whatever").touch()
    legealdirs = [
        "abc@cdef:1_0",
        "abc@cdef:2_1",
        "abc@cdef:3_2",
        "abc@cdef:4_3",
        "abc@cdef:5_1",
    ]
    bad_dirs = [
        "abc",
        "1_",
        "1_asdffdsa",
        "asdfas@fdasf",
        "1asdbsa@gdasf",
        "fdsaf@jl123",
        "-1_fdsaf@jl:_3",
        "_fdsaf@jl:3_",
        "_fdsaf@:",
        "@:_",
    ]
    for d in legealdirs:
        cwd.joinpath(d).mkdir()

    for d in bad_dirs:
        cwd.joinpath(d).mkdir()

    latest_img = cwd.joinpath("abc@cdef:5_1")
    for i in range(4):
        latest_img.joinpath("%d.dmtcp" % i).touch()


def test_images_in_dir(mktestdirs):

    images = checkpoint_manager.images_in_dir()
    expected = [
        "abc@cdef:1_0",
        "abc@cdef:2_1",
        "abc@cdef:3_2",
        "abc@cdef:4_3",
        "abc@cdef:5_1",
    ]
    assert images == expected


def test_latest_image_dir(tmpdir, mktestdirs):
    expected = os.path.join(tmpdir, "abc@cdef:5_1")
    assert checkpoint_manager.latest_image_dir() == expected


def test_images_in_latest(tmpdir, mktestdirs):
    latest_dir = checkpoint_manager.latest_image_dir()
    imgs = checkpoint_manager.image_files_in_dir(latest_dir)
    exp_imgs = [
        os.path.join(
            tmpdir,
            "abc@cdef:5_1",
            "%d.dmtcp" %
            i) for i in range(4)]
    assert exp_imgs == imgs


def test_Ckpt_manager_current_cktp_id_when_imgaes_exist(mktestdirs):
    general.destory_singleton(checkpoint_manager.CkptManager)
    m = checkpoint_manager.CkptManager(checkpoint_manager.KeepAll,
                                       "abc@cdef:5_1")
    assert m.next_ckpt_id() == (6, 5)
    assert m.next_ckpt_id() == (7, 6)

    general.destory_singleton(checkpoint_manager.CkptManager)
    m = checkpoint_manager.CkptManager(checkpoint_manager.KeepAll,
                                       "abc@cdef:4_3")
    assert m.next_ckpt_id() == (6, 4)
    assert m.next_ckpt_id() == (7, 6)


def test_Ckpt_manager_current_cktp_id_when_no_imgaes_exist(set_context):
    general.destory_singleton(checkpoint_manager.CkptManager)
    m = checkpoint_manager.CkptManager(checkpoint_manager.KeepAll)
    assert m.next_ckpt_id() == (1, 0)
    assert m.next_ckpt_id() == (2, 1)
    assert m.next_ckpt_id() == (3, 2)
