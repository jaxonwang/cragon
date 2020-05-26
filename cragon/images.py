import os
import json
import shutil
import glob
import pathlib

from cragon import context
from cragon import utils


def images_in_dir():
    pass


def latest_image():
    # TODO: use id
    images = list(pathlib.Path(context.image_dir).rglob("*.dmtcp"))
    if not images:
        return None
    images.sort(key=lambda x: os.path.getmtime(str(x)), reverse=True)
    return str(images[0])


def latest_image_dir():
    img = latest_image()
    if not img:
        return None
    return str(pathlib.Path(img).absolute().parent)


def get_unarchived_images():
    script_name = "dmtcp_restart_script*.sh"
    image_name = os.path.join(context.image_dir, "*.dmtcp")
    script_pattern = os.path.join(context.image_dir, script_name)
    files = glob.glob(image_name) + glob.glob(script_pattern)
    # when restart dmtcp will try to create shells in pwd
    files += glob.glob(os.path.join(context.cwd, script_name))
    return files


def archive_checkpoint(ckpt_timestamp, execution_info):

    execution_info["checkpint_timestamp"] = ckpt_timestamp

    ckpt_time_str = utils.format_time_to_readable(ckpt_timestamp)
    process_name = os.path.basename(execution_info["command"][0])
    archive_dir_name = "%s_%s_%s@%s" % (
        process_name, ckpt_time_str,
        context.current_user_name, context.current_host_name)
    archive_dir_path = os.path.join(context.image_dir, archive_dir_name)
    utils.create_dir_unless_exist(archive_dir_path)

    image_files = get_unarchived_images()
    for f in image_files:
        shutil.move(f, archive_dir_path)

    # record exe and ckpt info
    ckpt_info_file = os.path.join(archive_dir_path,
                                  context.ckpt_info_file_name)
    with open(ckpt_info_file, "w") as f:
        json.dump(execution_info, f, indent=2, sort_keys=True,
                  ensure_ascii=True)


class ImageUpdatePolicy(object):
    pass


class KeepLatestN(ImageUpdatePolicy):

    def __init__(self, N):
        pass


@utils.init_once_singleton
class ImagesManager(object):

    def __init__(self, ckpt_policy):
        self.ckpt_policy = ckpt_policy
