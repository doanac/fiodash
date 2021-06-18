from argparse import ArgumentParser
import logging

from bottle import error, redirect, request, route, run, template
from requests import HTTPError

from fiodash.aklite import AkliteClient
from fiodash.templates import INDEX_TPL

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger()
logging.getLogger("requests").setLevel(logging.WARNING)

client = AkliteClient()


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
    return template(INDEX_TPL, current_target=current, latest=latest, apps=apps)


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
        client.install(latest.name, correlation_id)
    redirect("/")


def _get_parser():
    parser = ArgumentParser(description="fiodash web app")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to. Default=%(default)s",
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port to bind to. Default=%(default)s",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Run in debug mode",
    )
    return parser


if __name__ == "__main__":
    parser = _get_parser()
    args = parser.parse_args()

    client.refresh_config()
    client.send_telemetry()
    run(host=args.host, port=args.port, debug=args.debug)
