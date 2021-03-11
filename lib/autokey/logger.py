# Copyright (C) 2018-2019 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
import logging.handlers
import pathlib
import sys

from autokey.argument_parser import Namespace
from autokey.common import APP_NAME, DATA_DIR

root_logger = logging.getLogger(APP_NAME)

MAX_LOG_SIZE = 5 * 2**20  # 5 megabytes
MAX_LOG_COUNT = 3
LOG_FORMAT = "%(asctime)s %(levelname)s - %(name)s - %(message)s"
LOG_FILE = pathlib.Path(DATA_DIR) / "autokey.log"


def get_logger(full_module_path: str) -> logging.Logger:
    module_path = ".".join(full_module_path.split(".")[1:])
    return root_logger.getChild(module_path)


def configure_root_logger(args: Namespace):
    """Initialise logging system"""
    root_logger.setLevel(1)
    pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=MAX_LOG_COUNT
    )
    file_handler.setLevel(logging.INFO)

    stdout_stream_handler = logging.StreamHandler(sys.stdout)
    logging_level = logging.INFO
    if args.verbose:
        logging_level = logging.DEBUG
    if args.mouse_logging:
        logging_level = 9
    
    stdout_stream_handler.setLevel(logging_level)
    stdout_stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger.addHandler(stdout_stream_handler)
    root_logger.addHandler(file_handler)
    if args.cutelog_integration:
        socket_handler = logging.handlers.SocketHandler("127.0.0.1", 19996)  # default listening address
        root_logger.addHandler(socket_handler)
        root_logger.info(f"""Connected logger "{root_logger.name}" to local log server.""")
