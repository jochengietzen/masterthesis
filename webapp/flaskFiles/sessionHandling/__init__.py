from webapp.flaskFiles.applicationProvider import app, server, session
import uuid
from webapp.helper import log
from datetime import timedelta

@app.server.before_first_request
def sessionPermanent():
    session.permanent = True
    server.permanent_session_lifetime = timedelta(weeks=4)

@app.server.before_request
def uid():
    if 'uid' not in session:
        log(session)
        session['uid'] = uuid.uuid4().__str__()
