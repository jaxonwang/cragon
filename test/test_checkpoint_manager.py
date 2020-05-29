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
        "3_abc@cdef",
        "2_abc@cdef",
        "1_abc@cdef",
        "5_abc@cdef",
    ]
    bad_dirs = [
        "abc",
        "1_",
        "1_asdffdsa",
        "asdfas@fdasf",
        "1asdbsa@gdasf",
        "dfasflj_fdsaf@jl",
        "-1_fdsaf@jl",
        "_fdsaf@jl",
        "_fdsaf@",
        "_@",
    ]
    for d in legealdirs:
        cwd.joinpath(d).mkdir()

    for d in bad_dirs:
        cwd.joinpath(d).mkdir()

    latest_img = cwd.joinpath("5_abc@cdef")
    for i in range(4):
        latest_img.joinpath("%d.dmtcp" % i).touch()


def test_images_in_dir(mktestdirs):

    images = checkpoint_manager.images_in_dir()
    expected = [
        "1_abc@cdef",
        "2_abc@cdef",
        "3_abc@cdef",
        "5_abc@cdef",
    ]
    assert images == expected


def test_latest_image_dir(tmpdir, mktestdirs):
    expected = os.path.join(tmpdir, "5_abc@cdef")
    assert checkpoint_manager.latest_image_dir() == expected


def test_images_in_latest(tmpdir, mktestdirs):
    latest_dir = checkpoint_manager.latest_image_dir()
    imgs = checkpoint_manager.image_files_in_dir(latest_dir)
    exp_imgs = [
        os.path.join(
            tmpdir,
            "5_abc@cdef",
            "%d.dmtcp" %
            i) for i in range(4)]
    assert exp_imgs == imgs


def test_Ckpt_manager_current_cktp_id_when_imgaes_exist(mktestdirs):
    general.destory_singleton(checkpoint_manager.CkptManager)
    m = checkpoint_manager.CkptManager(checkpoint_manager.KeepAll)
    assert m.next_ckpt_id() == 6


def test_Ckpt_manager_current_cktp_id_when_no_imgaes_exist(set_context):
    general.destory_singleton(checkpoint_manager.CkptManager)
    m = checkpoint_manager.CkptManager(checkpoint_manager.KeepAll)
    assert m.next_ckpt_id() == 1
