#!/usr/bin/python3
import logging
import os
import shlex
import subprocess
from time import sleep
from typing import Dict, List, NamedTuple, Optional
from uuid import uuid4

from docker.transport.unixconn import UnixHTTPAdapter
from requests import HTTPError, session

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger()
logging.getLogger("requests").setLevel(logging.WARNING)


class App(NamedTuple):
    uri: str


class Target(NamedTuple):
    name: str
    sha256: str
    version: int
    apps: Dict[str, App]

    @classmethod
    def from_dict(cls, data: dict) -> "Target":
        apps: Dict[str, App] = {}
        for app_name, app in (data.get("docker_compose_apps") or {}).items():
            apps[app_name] = App(app["uri"])
        return Target(data["name"], data["ostree-sha256"], data["version"], apps)

    def generate_correlation_id(self) -> str:
        return str(self.version) + "-" + str(uuid4())


class AkliteClient:
    def __init__(self):
        self.requests = session()
        self.requests.mount("http+unix://", UnixHTTPAdapter("/var/run/aklite.sock"))

    def refresh_config(self):
        r = self.requests.get("http+unix://localhost/config")
        r.raise_for_status()
        self._config = r.json()

    @property
    def polling_interval(self) -> int:
        return int(self._config["uptane"]["polling_sec"])

    @property
    def sota_dir(self) -> str:
        # Weird thing with how propertytree/json/toml does stuff:
        path = self._config["storage"]["path"]
        if path[0] == '"':
            # path is quoted
            path = path[1:-1]
        return path

    @property
    def configured_apps(self) -> List[str]:
        # Weird thing with how propertytree/json/toml does stuff:
        apps = self._config["pacman"].get("compose_apps") or ""
        if not apps:
            return []
        if apps[0] == '"':
            # path is quoted
            apps = apps[1:-1]
        return [x.strip() for x in apps.split(",")]

    def download(self, target: str, correlation_id: str, reason: str):
        data = {
            "target-name": target,
            "correlation-id": correlation_id,
            "reason": reason,
        }
        r = self.requests.post("http+unix://localhost/targets/download", json=data)
        r.raise_for_status()

    def get_current(self) -> Target:
        r = self.requests.get("http+unix://localhost/targets/current")
        r.raise_for_status()
        return Target.from_dict(r.json())

    def install(self, target: str, correlation_id: str) -> bool:
        data = {
            "target-name": target,
            "correlation-id": correlation_id,
        }
        r = self.requests.post("http+unix://localhost/targets/install", json=data)
        r.raise_for_status()
        if r.json().get("needs-reboot"):
            log.warning("Target installation requires reboot. Rebooting now!")
            return True
        return False

    def reboot(self):
        reboot_cmd = self._config["bootloader"]["reboot_command"]
        subprocess.check_call(shlex.split(reboot_cmd))

    def send_telemetry(self):
        r = self.requests.put("http+unix://localhost/telemetry")
        r.raise_for_status()

    def set_apps(self, apps: List[str]):
        data = {
            "apps": apps,
            "cfg-file": "z-59-fiodash.toml",
        }
        r = self.requests.post("http+unix://localhost/config/apps", json=data)
        r.raise_for_status()

    def targets(self) -> List[Target]:
        r = self.requests.get("http+unix://localhost/targets")
        r.raise_for_status()
        targets: List[Target] = []
        for item in r.json()["targets"]:
            targets.append(Target.from_dict(item))
        return targets
