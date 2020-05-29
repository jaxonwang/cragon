import os
import json
import shutil
import glob
import pathlib
import re

from cragon import context
from cragon import utils


def get_unarchived_images():
    script_name = "dmtcp_restart_script*.sh"
    image_name = os.path.join(context.ckpt_dir, "*.dmtcp")
    script_pattern = os.path.join(context.ckpt_dir, script_name)
    files = glob.glob(image_name) + glob.glob(script_pattern)
    # when restart dmtcp will try to create shells in pwd
    files += glob.glob(os.path.join(context.cwd, script_name))
    return files


def gen_image_dir_name(ckpt_id, username, hostname):
    return "%s_%s@%s" % (
        ckpt_id, username, hostname)


def extract_image_dir_name(image_dir_name):
    image_dir_name = pathlib.Path(image_dir_name).name
    p = re.compile("^([0-9]+)_(.+)@(.+)$")
    matched = p.match(image_dir_name)
    if not matched:
        return None
    else:
        return (matched.group(1),
                matched.group(2),
                matched.group(3))


def images_in_dir():
    # return the images in the directory, ordered from old to latest
    sub_dirs = [
        x for x in pathlib.Path(
            context.ckpt_dir).iterdir() if x.is_dir()]
    image_dirs = []
    for sub_dir in sub_dirs:
        extracted = extract_image_dir_name(sub_dir.name)
        if not extracted:
            continue
        img_id = extracted[0]
        image_dirs.append((sub_dir.name, img_id))
    image_dirs.sort(key=lambda x: x[1])
    return [i[0] for i in image_dirs]


def latest_image_dir():
    imgs = images_in_dir()
    if not imgs:
        return None
    latest = imgs[-1]
    return str(pathlib.Path(context.ckpt_dir).joinpath(latest).absolute())


def image_files_in_dir(img_dir):
    images = list(pathlib.Path(img_dir).glob("*.dmtcp"))
    return [str(i.absolute()) for i in images]


class ImageUpdatePolicy(object):
    pass


class KeepLatestN(ImageUpdatePolicy):

    def __init__(self, N):
        pass


class KeepAll(ImageUpdatePolicy):
    pass


@utils.init_once_singleton
class CkptManager(object):

    def __init__(self, ckpt_policy):
        self.ckpt_policy = ckpt_policy
        self.image_list = None

        self.init_records()

    def init_records(self):
        self.image_list = images_in_dir()
        if self.image_list:
            current_ckpt_id = extract_image_dir_name(self.image_list[-1])[0]
            self.current_ckpt_id = int(current_ckpt_id)
        else:
            # if dir is empty then start from 0
            self.current_ckpt_id = 0

    def next_ckpt_id(self):
        self.current_ckpt_id += 1
        return self.current_ckpt_id

    def make_checkpoint(self, ckpt_info):
        # record and archive the checkpoint of
        archive_dir_name = gen_image_dir_name(self.next_ckpt_id(),
                                              context.current_user_name,
                                              context.current_host_name)
        archive_dir_path = os.path.join(context.ckpt_dir, archive_dir_name)
        utils.create_dir_unless_exist(archive_dir_path)

        image_files = get_unarchived_images()
        for f in image_files:
            shutil.move(f, archive_dir_path)

        # record exe and ckpt info
        ckpt_info_file = os.path.join(archive_dir_path,
                                      context.ckpt_info_file_name)
        with open(ckpt_info_file, "w") as f:
            json.dump(ckpt_info, f, indent=2, sort_keys=True,
                      ensure_ascii=True)
