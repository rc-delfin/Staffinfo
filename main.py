import os
import requests
import oauthlib

from flask import (
    Flask,
    render_template,
    request, redirect, url_for, session, current_app
)
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
load_dotenv()

def _empty_session():
    """
    Deletes the Google token and clears the session
    """
    if "google" in current_app.blueprints and hasattr(
            current_app.blueprints["google"], "token"
    ):
        del current_app.blueprints["google"].token
    session.clear()

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
    redirect_to="staffinfo"
)

app.register_blueprint(google_bp, url_prefix="/login")

api_key = os.getenv("XAPI_SHH")
base_uri = os.getenv("BASE_URI")


def getStaffPic(resno):
    base_uri_get_pic = base_uri + "getpic?resno=" + resno
    headers = {"X-API-KEY": api_key}
    payload = {}
    response_pic = requests.request("GET", base_uri_get_pic, headers=headers, data=payload)
    print("response_pic: " + "got pic")  # response_pic.text)
    if response_pic == 'RESNO not found':
        return "RESNO not found"
    else:
        return response_pic.text


def getStaffInfo(resno):
    base_uri_get_info = base_uri + "getinfo_v2?resno=" + resno
    headers = {"X-API-KEY": api_key}
    payload = {}
    response_info = requests.request("GET", base_uri_get_info, headers=headers, data=payload)
    print("response_info: " + response_info.text)
    if response_info.text == "RESNO not found":
        return {
            "name": "-",
            "positionapptcat": "-",
            "profile": "",
            "resid": resno,
            "resource_type": "-",
            "start_date": "-"
        }
    else:
        return response_info.json()


@app.errorhandler(oauthlib.oauth2.rfc6749.errors.TokenExpiredError)
@app.errorhandler(oauthlib.oauth2.rfc6749.errors.InvalidClientIdError)
def token_expired(_):
    _empty_session()
    return redirect(url_for("login"))


# TOKEN ERROR HANDLING #
@app.errorhandler(404)
def page_not_found(self):
    return render_template(
        "error.html",
        error_message_title="Ooops...that's a 404 code",
        error_message="This is an IRRI managed page. The resource you were looking for cannot be found.",
    )


@app.errorhandler(500)
def template_not_found(self):
    return render_template(
        "error.html",
        error_message_title="Ooops...that's a 500 code",
        error_message="This is an IRRI managed page. The server encountered an unexpected condition.",
    )


@app.route('/staffinfo', methods=["GET", "POST"])
def index():
    session["resno"] = request.args.get("resno")
    if not google.authorized:
        return redirect(url_for("google.login"))
    return redirect(url_for("staffinfo", resno=session["resno"]))


@app.route('/info', methods=["GET", "POST"])
def staffinfo():
    # resno = session["resno"]
    # return resno
    resno = session["resno"]

    print("getting staff info..." + resno)
    staff_info = getStaffInfo(resno)
    name = staff_info["name"]
    if staff_info["resource_type"] == "NRS" or staff_info["resource_type"] == "GRS":
        label = "Position"
    else:
        label = "Appointment Category"
    label_value = staff_info["positionapptcat"]
    resource_type = staff_info["resource_type"]
    start_date = staff_info["start_date"]
    profile = staff_info["profile"]

    print("getting staff pic..." + resno)
    staff_pic = getStaffPic(resno)
    picture = "data:image/png;base64," + staff_pic

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


if __name__ == '__main__':
    app.run()
