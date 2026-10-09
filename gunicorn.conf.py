# Copyright (C) New Community Church SE London 2026.
# For licensing information see LICENSE.md

"""✨ How gunicorn serves Anville in the image (docs/server-approach.md). Development uses runserver."""

import os

wsgi_app = "config.wsgi:application"
bind = "0.0.0.0:8000"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))

# ✨ No access log, on purpose. An observer's or a coach's link carries its token or secret in the address,
# and whoever reads that in a log can answer as them. Errors still go to the server's output.
accesslog = None
errorlog = "-"

# ✨ gunicorn's control socket would be a file in the home directory, which the image's user does not need.
control_socket_disable = True

# ✨ Each worker touches a file to show it is alive. In a container that file belongs in memory: on the
# container's own disk the touch can stall, and gunicorn then takes a healthy worker for a hung one.
if os.path.isdir("/dev/shm"):
    worker_tmp_dir = "/dev/shm"
