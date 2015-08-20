
from collections import namedtuple
import contextlib
import logging
import os
import subprocess
import sys

import zmq

from .simplesetup import RemoteTeamPlayer

# silence stupid warnings from logging module
logging.root.manager.emittedNoHandlerWarning = 1
_logger = logging.getLogger("pelita.pelitagame")

TeamSpec = namedtuple("TeamSpec", ["module", "address"])
ModuleSpec = namedtuple("ModuleSpec", ["prefix", "module"])


def get_python_process():
    py_proc = sys.executable
    if not py_proc:
        raise RuntimeError("Cannot retrieve current Python executable.")
    return py_proc


class ModuleRunner(object):
    def __init__(self, team_spec):
        self.team_spec = team_spec

class DefaultRunner(ModuleRunner):
    def run(self, addr):
        player_path = os.path.dirname(sys.argv[0])
        player = os.path.join(player_path, "module_player.py")
        external_call = [get_python_process(),
                         player,
                         self.team_spec,
                         addr]
        _logger.debug("Executing: %r", external_call)
        return subprocess.Popen(external_call)

class Py2Runner(ModuleRunner):
    def run(self, addr):
        player_path = os.path.dirname(sys.argv[0])
        player = os.path.join(player_path, "module_player.py")
        external_call = ["python2",
                         player,
                         self.team_spec,
                         addr]
        _logger.debug("Executing: %r", external_call)
        return subprocess.Popen(external_call)

class Py3Runner(ModuleRunner):
    def run(self, addr):
        player_path = os.path.dirname(sys.argv[0])
        player = os.path.join(player_path, "module_player.py")
        external_call = ["python3",
                         player,
                         self.team_spec,
                         addr]
        _logger.debug("Executing: %r", external_call)
        return subprocess.Popen(external_call)


@contextlib.contextmanager
def _call_standalone_pelitagame(module_spec, address):
    proc = None
    try:
        proc = call_standalone_pelitagame(module_spec, address)
        yield proc
    finally:
        if proc is None:
            print("Problem running pelitagame")
        else:
            _logger.debug("Terminating proc %r", proc)
            proc.terminate()

def call_standalone_pelitagame(module_spec, address):
    """ Starts another process with the same Python executable,
    the same start script (pelitagame) and runs `team_spec`
    as a standalone client on URL `addr`.
    """
    defined_runners = {
        "py": DefaultRunner,
        "py2": Py2Runner,
        "py3": Py3Runner
    }

    if module_spec.prefix is not None:
        try:
            runner = defined_runners[module_spec.prefix]
        except KeyError:
            raise ValueError("Unknown runner: {}:".format(module_spec.prefix))
    else:
        runner = DefaultRunner

    return runner(module_spec.module).run(address)

def check_team(team_spec):
    ctx = zmq.Context()
    socket = ctx.socket(zmq.PAIR)

    if team_spec.module is None:
        _logger.info("Binding to %s", team_spec.address)
        socket.bind(team_spec.address)

    else:
        _logger.info("Binding to %s", team_spec.address)
        socket_port = socket.bind_to_random_port(team_spec.address)
        team_spec = team_spec._replace(address="%s:%d" % (team_spec.address, socket_port))

    team_player = RemoteTeamPlayer(socket)
    print(team_player)

    if team_spec.module:
        with _call_standalone_pelitagame(team_spec.module, team_spec.address):
            name = team_player.team_name()
    else:
        name = team_player.team_name()

    return name
