from app import app as application

from app import db
from app.models import *

@application.shell_context_processor
def make_shell_context():
    return {
        'app': application,
        'db': db,
    }

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=8888)