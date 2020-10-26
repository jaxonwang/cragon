import os
import logging
import json
import shutil
import glob
import pathlib
import re

from cragon import context
from cragon import utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_unarchived_images():
    script_name = "dmtcp_restart_script*.sh"
    image_name = os.path.join(context.ckpt_dir, "*.dmtcp")
    script_pattern = os.path.join(context.ckpt_dir, script_name)
    files = glob.glob(image_name) + glob.glob(script_pattern)
    # when restart dmtcp will try to create shells in pwd
    files += glob.glob(os.path.join(context.cwd, script_name))
    return files


def gen_image_dir_name(username, hostname, global_id, parent_id):
    return "%s@%s:%d_%d" % (username, hostname, global_id, parent_id)


# dir pattern : user@host:id_parentofthisid
dir_name_pattern = re.compile("^(.+)@(.+):([0-9]+)_([0-9]+)$")


class Image(object):

    def __init__(self, user, host, global_id, parent_id):
        """Image class to store basic info of image.
        Arguments:
        user -- user who make this checkpoint
        host -- the machine where this checkpoint was made
        global_id -- global unique id of one run
        parent_id -- last checkpoint before the point when this restart from
        """
        self.user = user
        self.host = host
        self.global_id = int(global_id)
        self.parent_id = int(parent_id)


def extract_image_dir_name(image_dir_name):
    image_dir_name = pathlib.Path(image_dir_name).name
    matched = dir_name_pattern.match(image_dir_name)
    if not matched:
        return None
    else:
        return Image(user=matched[1], host=matched[2],
                     global_id=matched[3], parent_id=matched[4])


def images_in_dir(ckpt_dir):
    # return the images in the directory, ordered from old to latest
    sub_dirs = [
        x for x in pathlib.Path(ckpt_dir).iterdir() if x.is_dir()]
    image_dirs = []
    for sub_dir in sub_dirs:
        extracted_image = extract_image_dir_name(sub_dir.name)
        if not extracted_image:
            continue
        img_id = extracted_image.global_id
        image_dirs.append((sub_dir.name, img_id))
    image_dirs.sort(key=lambda x: x[1])
    return [i[0] for i in image_dirs]


def latest_image_dir(ckpt_dir):
    imgs = images_in_dir(ckpt_dir)
    if not imgs:
        return None
    latest = imgs[-1]
    return str(pathlib.Path(ckpt_dir).joinpath(latest).absolute())


def image_files_in_image_dir(img_dir):
    images = list(pathlib.Path(img_dir).glob("*.dmtcp"))
    # sort to make sure return the same file list for a dir
    return sorted([str(i.absolute()) for i in images])


class ImageUpdatePolicy(object):
    pass


class KeepLatestN(ImageUpdatePolicy):

    def __init__(self, N):
        """Keep the latest N images policy."""
        pass


class KeepAll(ImageUpdatePolicy):
    pass


@utils.init_once_singleton
class CkptManager(object):

    def __init__(self, ckpt_policy, image_dir_to_restart=None):
        """who controls everything of checkpoint and related images."""
        self.ckpt_policy = ckpt_policy
        self.image_list = None
        logger.info("Set the checkpoint image management policy: %s",
                    ckpt_policy.__name__)

        self.restart_from = image_dir_to_restart
        self.init_records()

    def init_records(self):
        self.image_list = images_in_dir(context.ckpt_dir)
        if self.image_list:
            latest_image = extract_image_dir_name(self.image_list[-1])

            self.next_image_global_id = latest_image.global_id + 1
            image_restart_from = extract_image_dir_name(self.restart_from)
            # parent point to the last checkpoint image recovered from
            self.next_image_parent_id = image_restart_from.global_id
            logging.debug("Images found: %s" % str(self.image_list))
        else:
            # if dir is empty then start from 0
            self.next_image_global_id = 1
            self.next_image_parent_id = 0
        logging.info("Set the current checkpoint id to :%d, and its parent %d",
                     self.next_image_global_id, self.next_image_parent_id)

    def next_ckpt_id(self):
        ret_global_id = self.next_image_global_id
        ret_parent_id = self.next_image_parent_id

        self.next_image_global_id += 1
        self.next_image_parent_id = ret_global_id
        return ret_global_id, ret_parent_id

    def make_checkpoint(self, ckpt_tmp_dir, ckpt_info):
        # record and archive the checkpoint of
        g_id, p_id = self.next_ckpt_id()
        archive_dir_name = gen_image_dir_name(context.current_user_name,
                                              context.current_host_name,
                                              g_id, p_id)
        archive_dir_path = context.DirStructure.ckpt_dir_to_image_dir(
            context.ckpt_dir, archive_dir_name)

        # move the ckpt images from tmp dir to archive dir
        shutil.move(ckpt_tmp_dir, archive_dir_path)
        # Caution: this should be atomic but I don't bother to do that,
        # assume this move and create is fast enough and dmtcp won't notice the
        # change
        utils.create_dir_unless_exist(ckpt_tmp_dir)

        logger.info("Archiving current checkpoint images to %s" %
                    archive_dir_path)
        # record exe and ckpt info
        ckpt_info_file = \
            context.DirStructure.image_dir_to_ckpt_info_file(archive_dir_path)
        with open(ckpt_info_file, "w") as f:
            json.dump(ckpt_info, f, indent=2, sort_keys=True,
                      ensure_ascii=True)
