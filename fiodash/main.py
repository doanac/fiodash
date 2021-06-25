from argparse import ArgumentParser
import logging
import os
import sys
from threading import Thread
from time import sleep

from bottle import error, redirect, request, response, route, run, template
from requests import HTTPError

from fiodash.aklite import AkliteClient
from fiodash.templates import INDEX_TPL

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger()
logging.getLogger("requests").setLevel(logging.WARNING)

client = AkliteClient()
SINGLE_APP = os.environ.get("FIODASH_SINGLE_APP")


@error(500)
def error500(error):
    if isinstance(error.exception, HTTPError):
        r = error.exception.response
        return f"HTTP_{r.status_code}: {r.text}"
    return str(error.exception)


@route("/")
def index():
    current = client.get_current()
    latest = client.targets()[-1]
    update_available = None

    client.refresh_config()
    configured_apps = client.configured_apps
    apps = []
    for app in current.apps:
        apps.append({"name": app, "enabled": app in configured_apps})
    return template(
        INDEX_TPL,
        current_target=current,
        latest=latest,
        apps=apps,
        single_app=SINGLE_APP,
    )


@route("/update-apps", method="POST")
def update_apps():
    apps = []
    request_apps = request.json["apps"]
    for app in client.get_current().apps:
        if app in request_apps:
            apps.append(app)

    if set(apps) != set(client.configured_apps):
        log.info("Enabling apps: %s", apps)
        client.set_apps(apps)
    redirect("/")


@route("/update-target", method="POST")
def update_target():
    current = client.get_current()
    latest = client.targets()[-1]
    log.info("Latest target is %s", latest)
    if current.name != latest.name:
        log.info("Downloading target")
        correlation_id = latest.generate_correlation_id()
        reason = f"Upgrading from {current.name} to {latest.name}"
        client.download(latest.name, correlation_id, reason)

        log.info("Installing target")
        if client.install(latest.name, correlation_id):
            response.status = 202

            def sleep_reboot():
                sleep(2)
                client.reboot()

            Thread(target=sleep_reboot).start()
    return ""


def webapp(args):
    run(host=args.host, port=args.port, debug=args.debug, reloader=args.debug)


def list_targets(args):
    for t in client.targets():
        print("# Target version", t.version)
        print("\tname:      ", t.name)
        print("\tostree sha:", t.sha256)
        print("\tapps:")
        for name, app in t.apps.items():
            print("\t\t", name, "\t", app.uri)
        print()


def install_target(args):
    current = client.get_current()
    targets = client.targets()
    tgt = targets[-1]
    if args.target_version:
        for t in targets:
            if t.version == args.target_version:
                tgt = t
                break
        else:
            sys.exit("Target version not found")

    log.info("Downloading %s", tgt.name)
    correlation_id = tgt.generate_correlation_id()
    reason = f"Upgrading from {current.name} to {tgt.name}"
    client.download(tgt.name, correlation_id, reason)

    log.info("Installing %s", tgt)
    if client.install(tgt.name, correlation_id):
        client.reboot()


def set_apps(args):
    client.set_apps(args.app)


def status(args):
    t = client.get_current()
    configured_apps = client.configured_apps
    print("# Target version", t.version)
    print("\tname:      ", t.name)
    print("\tostree sha:", t.sha256)
    print("\tapps: (* = running)")
    for name, app in t.apps.items():
        val = "*" if name in configured_apps else " "
        print("\t\t", val, name, "\t", app.uri)


def _get_parser():
    parser = ArgumentParser(description="fiodash web app")
    sub = parser.add_subparsers(help="sub-command help")

    p = sub.add_parser("serve", help="Run as a web app")
    p.set_defaults(func=webapp)
    p.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to. Default=%(default)s",
    )
    p.add_argument(
        "--port", type=int, default=8080, help="Port to bind to. Default=%(default)s",
    )
    p.add_argument(
        "--debug", action="store_true", help="Run in debug mode",
    )

    p = sub.add_parser("list", help="List available targets")
    p.set_defaults(func=list_targets)

    p = sub.add_parser("set-apps", help="Set apps to run on target")
    p.set_defaults(func=set_apps)
    p.add_argument("app", nargs="*")

    p = sub.add_parser("install", help="Install target")
    p.set_defaults(func=install_target)
    p.add_argument(
        "--target-version",
        "-t",
        type=int,
        help="Target version. Default is latest Target",
    )

    p = sub.add_parser("status", help="Show current status")
    p.set_defaults(func=status)

    return parser


def main():
    parser = _get_parser()
    args = parser.parse_args()

    client.refresh_config()
    client.send_telemetry()

    args = parser.parse_args()
    if getattr(args, "func", None):
        args.func(args)
    else:
        parser.print_help(sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
