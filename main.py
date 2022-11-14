import requests
import os
import oauthlib
import json


from flask import (
    Flask,
    render_template,
    request, redirect, url_for, session, current_app
)
# from flask_dance.consumer import requests

from flask_dance.contrib.google import make_google_blueprint, google

# oauth
from oauthlib.oauth2.rfc6749.errors import InvalidClientIdError, TokenExpiredError
# os.environ
from dotenv import load_dotenv

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
load_dotenv()


def _empty_session():
    """
    Deletes the google token and clears the session
    """
    if "google" in current_app.blueprints and hasattr(
            current_app.blueprints["google"], "token"
    ):
        del current_app.blueprints["google"].token
    session.clear()


def getHRinfo(email, ocs_url, ocs_hdr_key):
    def dd(hh):
        return str(float(hh) / 8.0)

    url = ocs_url
    payload = {"email": email}
    headers = {"X-API-KEY": ocs_hdr_key}

    r = requests.get(url, params=payload, headers=headers)
    lst = r.text.split("\t")

    d = {}

    if lst:
        leaves = lst[1:]
        for num, name in enumerate(
                leaves
        ):  # name is an unused variable but app crashes if removed
            if num % 2 == 0:
                d[leaves[num]] = [leaves[num + 1], dd(leaves[num + 1])]
            else:
                continue
    return [lst[0], d]


app = Flask(__name__)
app.config["SECRET_KEY"] = "quizbeeapp123456789"

back_home = os.environ.get("BACK_HOME")
google_bp = make_google_blueprint(
    client_id=os.getenv("GOO_CLIENT"),
    client_secret=os.getenv("GOO_SHH"),
    scope=[
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_to="landing_page",
)

app.register_blueprint(google_bp, url_prefix="/login")


@app.errorhandler(oauthlib.oauth2.rfc6749.errors.TokenExpiredError)
@app.errorhandler(oauthlib.oauth2.rfc6749.errors.InvalidClientIdError)
def token_expired(_):
    _empty_session()
    return redirect(url_for("landing_page"))


# TOKEN ERROR HANDLING #
@app.errorhandler(404)
def page_not_found(self):
    return render_template(
        "error.html",
        error_message_title="Ooops...that's a 404 HTML code",
        error_message="You seem to be missing some text. Maybe a resno?",
    )


@app.errorhandler(500)
def template_not_found(self):
    return render_template(
        "error.html",
        error_message_title="Ooops...that's a 500 HTML code",
        error_message="You seem to be missing some text. Maybe a resno?",
    )


@app.route('/', methods=["GET", "POST"])
def landing_page():
    if not google.authorized:
        return redirect(url_for("google.login"))

    return render_template(
            'index.html',
        )


@app.route('/staffinfo/<resno>', methods=["GET", "POST"])
def staffinfo(resno):
    if not google.authorized:
        return redirect(url_for("google.login"))

    if resno != "":
        resp = google.get("/oauth2/v2/userinfo")
        assert resp.ok, resp.text

        payload = {}
        api_key = os.getenv("XAPI_SHH")
        base_uri = os.getenv("BASE_URI")
        base_uri_get_pic = base_uri + "getpic?resno=" + resno
        base_uri_get_info = base_uri + "getinfo?resno=" + resno
        headers = {"X-API-KEY": api_key}
        response_pic = requests.request("GET", base_uri_get_pic, headers=headers, data=payload)
        response_info = requests.request("GET", base_uri_get_info, headers=headers, data=payload)
        print(json.loads(response_info.text))
        staff_info=json.loads(response_info.text)

        resno = staff_info["resno"]
        name = staff_info["name"]
        label = staff_info["label"]
        label_value = staff_info["label_value"]
        resource_type = staff_info["resource_type"]
        start_date = staff_info["start_date"]
        profile = staff_info["profile"]
        # session["picture"] = "data:image/png;base64," + r.text
        picture = "data:image/png;base64," + response_pic.text

        return render_template(
            'staffinfo.html',
            resno=resno,
            name=name,
            label=label,
            label_value=label_value,
            resource_type=resource_type,
            start_date=start_date,
            profile=profile,
            picture=picture,
        )

    else:
        return render_template(
            'error.html',
            error_message_title="Error",
            error_message="An error has occurred. Please contact MIS.",
        )


if __name__ == '__main__':
    app.run()
