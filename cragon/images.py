import os
import shutil
import glob
import pathlib

from cragon import context
from cragon import utils


def images_in_dir():
    pass


def latest_images():
    # TODO: use id
    images = list(pathlib.Path(context.image_dir).rglob("*.dmtcp"))
    if not images:
        return None
    images.sort(key=lambda x: os.path.getmtime(str(x)), reverse=True)
    return str(images[0])


def get_unarchived_images():
    image_name = os.path.join(context.image_dir, "*.dmtcp")
    script_name = os.path.join(context.image_dir, "*.sh")
    files = glob.glob(image_name) + glob.glob(script_name)
    return files


def archive_current_image(ckpt_timestamp, process_name):
    ckpt_time_str = utils.format_time_to_readable(ckpt_timestamp)
    archive_dir_name = "%s_%s_%s@%s" % (
        os.path.basename(process_name), ckpt_time_str,
        context.current_user_name, context.current_host_name)
    archive_dir_path = os.path.join(context.image_dir, archive_dir_name)
    utils.create_dir_unless_exist(archive_dir_path)

    image_files = get_unarchived_images()
    for f in image_files:
        shutil.move(f, archive_dir_path)


class ImageUpdatePolicy(object):
    pass


class KeepLatestN(ImageUpdatePolicy):

    def __init__(self, N):
        pass


@utils.init_once_singleton
class ImagesManager(object):

    def __init__(self, ckpt_policy):
        self.ckpt_policy = ckpt_policy
