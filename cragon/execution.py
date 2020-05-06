import context
from utils import FATAL


class DMTCPCmdOption(object):

    def __init__(self):
        self.options = {}

    def set_new_coordinator(self):
        self.options["--new-coordinator"] = ""

    def set_plugin(self):
        if not context.dmtcp_plugins:
            FATAL("DMTCP plugin is missing!")
        self.options["--with-plugin"] = context.dmtcp_plugins

    def gen_options(self):
        opts = []
        for key, value in self.options.items():
            opts.append(key)
            if value:
                opts.append(value)
        return opts


class DMTCPrun(DMTCPCmdOption):
    def gen_options(self):
        self.set_new_coordinator()
        self.set_plugin()
        return super().gen_options()


class Execution(object):

    def start(self):
        pass


class FirstRun(Execution):
    def __init__(self, command_to_run):
        self.command_to_run = command_to_run
        self.dmtcp_cmd = [context.dmtcp_launch]
        self.dmtcp_cmd += DMTCPrun().gen_options()
        for c in command_to_run:
            self.dmtcp_cmd.append(c)
        print(self.dmtcp_cmd)
