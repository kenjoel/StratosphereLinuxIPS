import os
from flask import Flask, render_template, redirect, url_for, current_app

from slips_files.common.parsers.config_parser import ConfigParser
from .database.database import __database__
from .database.signals import message_sent
from .analysis.analysis import analysis
from .general.general import general
from .documentation.documentation import documentation
from .utils import read_db_file

RUNNING_IN_DOCKER = os.environ.get("IS_IN_A_DOCKER_CONTAINER", False)


def create_app():
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False  # disable sorting of timewindows
    return app


app = create_app()


@app.route("/redis")
def read_redis_port():
    res = read_db_file()
    return {"data": res}


@app.route("/")
def index():
    return render_template("app.html", title="Slips")


@app.route("/db/<new_port>")
def get_post_javascript_data(new_port):
    message_sent.send(
        current_app._get_current_object(), port=int(new_port), dbnumber=0
    )
    return redirect(url_for("index"))


@app.route("/info")
def set_pcap_info():
    """
    Set information about the pcap.
    """
    info = __database__.db.hgetall("analysis")

    profiles = __database__.db.smembers("profiles")
    info["num_profiles"] = len(profiles) if profiles else 0

    alerts_number = __database__.db.get("number_of_alerts")
    info["num_alerts"] = int(alerts_number) if alerts_number else 0

    return info


if __name__ == "__main__":
    app.register_blueprint(analysis, url_prefix="/analysis")

    app.register_blueprint(general, url_prefix="/general")

    app.register_blueprint(documentation, url_prefix="/documentation")

    if RUNNING_IN_DOCKER:
        host = "127.0.0.1"
    else:
        host = "0.0.0.0"
    app.run(host=host, port=ConfigParser().web_interface_port)
