# Real Aim2Build Files For Part Scanner

CATEGORY: R2

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.github/README.md 

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:

Copy target:
imports/real_existing/r2/README.md_

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi/datastructures.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
from collections.abc import Mapping
from typing import (
from annotated_doc import Doc
from pydantic import GetJsonSchemaHandler
from starlette.datastructures import URL as URL  # noqa: F401
from starlette.datastructures import Address as Address  # noqa: F401
from starlette.datastructures import FormData as FormData  # noqa: F401
from starlette.datastructures import Headers as Headers  # noqa: F401
from starlette.datastructures import QueryParams as QueryParams  # noqa: F401
from starlette.datastructures import State as State  # noqa: F401
from starlette.datastructures import UploadFile as StarletteUploadFile

Copy target:
imports/real_existing/r2/datastructures.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.9/site-packages/fastapi/datastructures.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
from typing import (
from annotated_doc import Doc
from fastapi._compat import (
from starlette.datastructures import URL as URL  # noqa: F401
from starlette.datastructures import Address as Address  # noqa: F401
from starlette.datastructures import FormData as FormData  # noqa: F401
from starlette.datastructures import Headers as Headers  # noqa: F401
from starlette.datastructures import QueryParams as QueryParams  # noqa: F401
from starlette.datastructures import State as State  # noqa: F401
from starlette.datastructures import UploadFile as StarletteUploadFile
from typing_extensions import Annotated

Copy target:
imports/real_existing/r2/datastructures.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.9/site-packages/setuptools/_distutils/command/upload.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
import os
import io
import hashlib
from base64 import standard_b64encode
from urllib.request import urlopen, Request, HTTPError
from urllib.parse import urlparse
from distutils.errors import DistutilsError, DistutilsOptionError
from distutils.core import PyPIRCCommand
from distutils.spawn import spawn
from distutils import log

Copy target:
imports/real_existing/r2/upload.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.9/site-packages/setuptools/command/upload_docs.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
from base64 import standard_b64encode
from distutils import log
from distutils.errors import DistutilsOptionError
import os
import socket
import zipfile
import tempfile
import shutil
import itertools
import functools
import http.client
import urllib.parse
from pkg_resources import iter_entry_points
from .upload import upload

Copy target:
imports/real_existing/r2/upload_docs.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/.venv/lib/python3.11/site-packages/fastapi/datastructures.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
from collections.abc import Mapping
from typing import (
from annotated_doc import Doc
from pydantic import GetJsonSchemaHandler
from starlette.datastructures import URL as URL  # noqa: F401
from starlette.datastructures import Address as Address  # noqa: F401
from starlette.datastructures import FormData as FormData  # noqa: F401
from starlette.datastructures import Headers as Headers  # noqa: F401
from starlette.datastructures import QueryParams as QueryParams  # noqa: F401
from starlette.datastructures import State as State  # noqa: F401
from starlette.datastructures import UploadFile as StarletteUploadFile

Copy target:
imports/real_existing/r2/datastructures.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/.venv/lib/python3.11/site-packages/pip/_vendor/distlib/index.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
from . import DistlibException
from .compat import (HTTPBasicAuthHandler, Request, HTTPPasswordMgr,
from .util import zip_dir, ServerProxy

Copy target:
imports/real_existing/r2/index.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/.venv/lib/python3.11/site-packages/setuptools/_distutils/command/upload.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
import os
import io
import hashlib
from base64 import standard_b64encode
from urllib.request import urlopen, Request, HTTPError
from urllib.parse import urlparse
from distutils.errors import DistutilsError, DistutilsOptionError
from distutils.core import PyPIRCCommand
from distutils.spawn import spawn
from distutils import log

Copy target:
imports/real_existing/r2/upload.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/.venv/lib/python3.11/site-packages/setuptools/command/upload_docs.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
from base64 import standard_b64encode
from distutils import log
from distutils.errors import DistutilsOptionError
import os
import socket
import zipfile
import tempfile
import shutil
import itertools
import functools
import http.client
import urllib.parse
import warnings
from .._importlib import metadata
from .. import SetuptoolsDeprecationWarning
from .upload import upload

Copy target:
imports/real_existing/r2/upload_docs.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/app/routers/buildability_discover.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from app.catalog_db import db
from app.routers.auth import User, get_current_user
from app.routers.buildability import _load_inventory_json  # MUST match compare source

Copy target:
imports/real_existing/r2/buildability_discover.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/scripts/import_lego_buy_sets.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
from __future__ import annotations
import argparse
import gzip
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from app.buy_sets_parts import resolve_num_parts  # noqa: E402
from app.lego_product_scrape import extract_piece_count_from_html, fetch_lego_piece_count  # noqa: E402
from app.paths import DATA_DIR  # noqa: E402

Copy target:
imports/real_existing/r2/import_lego_buy_sets.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/venv/lib/python3.9/site-packages/fastapi/datastructures.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
from typing import (
from annotated_doc import Doc
from fastapi._compat import (
from starlette.datastructures import URL as URL  # noqa: F401
from starlette.datastructures import Address as Address  # noqa: F401
from starlette.datastructures import FormData as FormData  # noqa: F401
from starlette.datastructures import Headers as Headers  # noqa: F401
from starlette.datastructures import QueryParams as QueryParams  # noqa: F401
from starlette.datastructures import State as State  # noqa: F401
from starlette.datastructures import UploadFile as StarletteUploadFile
from typing_extensions import Annotated

Copy target:
imports/real_existing/r2/datastructures.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/venv/lib/python3.9/site-packages/setuptools/_distutils/command/upload.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
import os
import io
import hashlib
from base64 import standard_b64encode
from urllib.request import urlopen, Request, HTTPError
from urllib.parse import urlparse
from distutils.errors import DistutilsError, DistutilsOptionError
from distutils.core import PyPIRCCommand
from distutils.spawn import spawn
from distutils import log

Copy target:
imports/real_existing/r2/upload.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/venv/lib/python3.9/site-packages/setuptools/command/upload_docs.py

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
from base64 import standard_b64encode
from distutils import log
from distutils.errors import DistutilsOptionError
import os
import socket
import zipfile
import tempfile
import shutil
import itertools
import functools
import http.client
import urllib.parse
from pkg_resources import iter_entry_points
from .upload import upload

Copy target:
imports/real_existing/r2/upload_docs.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/frontend/android/app/build/intermediates/assets/debug/mergeDebugAssets/public/assets/index-DZcoH_t1.js

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:

Copy target:
imports/real_existing/r2/index-DZcoH_t1.js

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/frontend/android/app/build/intermediates/assets/release/mergeReleaseAssets/public/assets/index-DZcoH_t1.js

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:

Copy target:
imports/real_existing/r2/index-DZcoH_t1.js

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/frontend/android/app/src/main/assets/public/assets/index-DZcoH_t1.js

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:

Copy target:
imports/real_existing/r2/index-DZcoH_t1.js

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/frontend/dist/assets/index-DKlgowf1.js

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:

Copy target:
imports/real_existing/r2/index-DKlgowf1.js

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/frontend/ios/App/App/public/assets/index-BhlQJyaZ.js

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:

Copy target:
imports/real_existing/r2/index-BhlQJyaZ.js

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/frontend/src/pages/PrivacyPage.tsx

Purpose:
Matched real Aim2Build implementation for R2.

Dependencies:
import React from "react";
import V2LegalLayout from "../v2/components/V2LegalLayout";

Copy target:
imports/real_existing/r2/PrivacyPage.tsx

CATEGORY: Azure

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.claude/settings.local.json

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:

Copy target:
imports/real_existing/azure/settings.local.json

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/annotated_types-0.7.0.dist-info/METADATA

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from typing import Annotated
from annotated_types import Gt, Len, Predicate
from annotated_types import Unit
from typing import Annotated, TypeVar, Callable, Any, get_origin, get_args
import pint
import astropy.units as u
from dataclasses import dataclass
from typing import Iterator
from annotated_types import GroupedMetadata, Ge

Copy target:
imports/real_existing/azure/METADATA

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/annotated_types/__init__.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
import math
import sys
import types
from dataclasses import dataclass
from datetime import tzinfo
from typing import TYPE_CHECKING, Any, Callable, Iterator, Optional, SupportsFloat, SupportsIndex, TypeVar, Union

Copy target:
imports/real_existing/azure/__init__.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_fileio.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from __future__ import annotations
import os
import pathlib
import sys
from collections.abc import (
from dataclasses import dataclass
from functools import partial
from os import PathLike
from typing import (
from .. import to_thread
from ..abc import AsyncResource

Copy target:
imports/real_existing/azure/_fileio.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/click/__init__.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from __future__ import annotations
from .core import Argument as Argument
from .core import Command as Command
from .core import CommandCollection as CommandCollection
from .core import Context as Context
from .core import Group as Group
from .core import Option as Option
from .core import Parameter as Parameter
from .decorators import argument as argument
from .decorators import command as command
from .decorators import confirmation_option as confirmation_option
from .decorators import group as group
from .decorators import help_option as help_option
from .decorators import make_pass_decorator as make_pass_decorator
from .decorators import option as option
from .decorators import pass_context as pass_context
from .decorators import pass_obj as pass_obj
from .decorators import password_option as password_option
from .decorators import version_option as version_option
from .exceptions import Abort as Abort
from .exceptions import BadArgumentUsage as BadArgumentUsage
from .exceptions import BadOptionUsage as BadOptionUsage
from .exceptions import BadParameter as BadParameter
from .exceptions import ClickException as ClickException
from .exceptions import FileError as FileError
from .exceptions import MissingParameter as MissingParameter
from .exceptions import NoSuchOption as NoSuchOption
from .exceptions import UsageError as UsageError
from .formatting import HelpFormatter as HelpFormatter
from .formatting import wrap_text as wrap_text
from .globals import get_current_context as get_current_context
from .termui import clear as clear
from .termui import confirm as confirm
from .termui import echo_via_pager as echo_via_pager
from .termui import edit as edit
from .termui import getchar as getchar
from .termui import launch as launch
from .termui import pause as pause
from .termui import progressbar as progressbar
from .termui import prompt as prompt

Copy target:
imports/real_existing/azure/__init__.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/click/decorators.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from __future__ import annotations
import inspect
import typing as t
from functools import update_wrapper
from gettext import gettext as _
from .core import Argument
from .core import Command
from .core import Context
from .core import Group
from .core import Option
from .core import Parameter
from .globals import get_current_context
from .utils import echo

Copy target:
imports/real_existing/azure/decorators.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/click/shell_completion.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from __future__ import annotations
import collections.abc as cabc
import os
import re
import typing as t
from gettext import gettext as _
from .core import Argument
from .core import Command
from .core import Context
from .core import Group
from .core import Option
from .core import Parameter
from .core import ParameterSource
from .utils import echo

Copy target:
imports/real_existing/azure/shell_completion.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/dns/_features.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
import importlib.metadata
import itertools
import string
from typing import Dict, List, Tuple

Copy target:
imports/real_existing/azure/_features.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/email_validator/validate_email.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from typing import Optional, Union, TYPE_CHECKING
import unicodedata
from .exceptions import EmailSyntaxError
from .types import ValidatedEmail
from .syntax import split_email, validate_email_local_part, validate_email_domain_name, validate_email_domain_literal, validate_email_length
from .rfc_constants import CASE_INSENSITIVE_MAILBOX_NAMES

Copy target:
imports/real_existing/azure/validate_email.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi/_compat/v2.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
import re
import warnings
from collections.abc import Sequence
from copy import copy, deepcopy
from dataclasses import dataclass, is_dataclass
from enum import Enum
from functools import lru_cache
from typing import (
from fastapi._compat import shared
from fastapi.openapi.constants import REF_TEMPLATE
from fastapi.types import IncEx, ModelNameMap, UnionType
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, create_model
from pydantic import PydanticSchemaGenerationError as PydanticSchemaGenerationError
from pydantic import PydanticUndefinedAnnotation as PydanticUndefinedAnnotation
from pydantic import ValidationError as ValidationError
from pydantic._internal._schema_generation_shared import (  # type: ignore[attr-defined]
from pydantic._internal._typing_extra import eval_type_lenient
from pydantic._internal._utils import lenient_issubclass as lenient_issubclass
from pydantic.fields import FieldInfo as FieldInfo
from pydantic.json_schema import GenerateJsonSchema as GenerateJsonSchema
from pydantic.json_schema import JsonSchemaValue as JsonSchemaValue
from pydantic_core import CoreSchema as CoreSchema
from pydantic_core import PydanticUndefined, PydanticUndefinedType
from pydantic_core import Url as Url
from typing_extensions import Literal, get_args, get_origin

Copy target:
imports/real_existing/azure/v2.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi/applications.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from collections.abc import Awaitable, Coroutine, Sequence
from enum import Enum
from typing import (
from annotated_doc import Doc
from fastapi import routing
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.exception_handlers import (
from fastapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from fastapi.logger import logger
from fastapi.middleware.asyncexitstack import AsyncExitStackMiddleware
from fastapi.openapi.docs import (
from fastapi.openapi.utils import get_openapi
from fastapi.params import Depends
from fastapi.types import DecoratedCallable, IncEx
from fastapi.utils import generate_unique_id
from starlette.applications import Starlette
from starlette.datastructures import State
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, ExceptionHandler, Lifespan, Receive, Scope, Send
from typing_extensions import deprecated

Copy target:
imports/real_existing/azure/applications.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi/openapi/utils.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
import http.client
import inspect
import warnings
from collections.abc import Sequence
from typing import Any, Optional, Union, cast
from fastapi import routing
from fastapi._compat import (
from fastapi.datastructures import DefaultPlaceholder
from fastapi.dependencies.models import Dependant
from fastapi.dependencies.utils import (
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import FastAPIDeprecationWarning
from fastapi.openapi.constants import METHODS_WITH_BODY, REF_PREFIX
from fastapi.openapi.models import OpenAPI
from fastapi.params import Body, ParamTypes
from fastapi.responses import Response
from fastapi.types import ModelNameMap
from fastapi.utils import (
from pydantic import BaseModel
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute
from typing_extensions import Literal

Copy target:
imports/real_existing/azure/utils.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi/routing.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
import email.message
import functools
import inspect
import json
from collections.abc import (
from contextlib import AsyncExitStack, asynccontextmanager
from enum import Enum, IntEnum
from typing import (
from annotated_doc import Doc
from fastapi import params
from fastapi._compat import (
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.dependencies.models import Dependant
from fastapi.dependencies.utils import (
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import (
from fastapi.types import DecoratedCallable, IncEx
from fastapi.utils import (
from starlette import routing
from starlette._exception_handler import wrap_app_handling_exceptions
from starlette._utils import is_async_callable
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import (
from starlette.routing import Mount as Mount  # noqa
from starlette.types import AppType, ASGIApp, Lifespan, Receive, Scope, Send
from starlette.websockets import WebSocket
from typing_extensions import deprecated

Copy target:
imports/real_existing/azure/routing.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip-25.3.dist-info/RECORD

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:

Copy target:
imports/real_existing/azure/RECORD

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/build_env.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from __future__ import annotations
import logging
import os
import pathlib
import site
import sys
import textwrap
from collections import OrderedDict
from collections.abc import Iterable
from types import TracebackType
from typing import TYPE_CHECKING, Protocol, TypedDict
from pip._vendor.packaging.version import Version
from pip import __file__ as pip_location
from pip._internal.cli.spinners import open_spinner
from pip._internal.locations import get_platlib, get_purelib, get_scheme
from pip._internal.metadata import get_default_environment, get_environment
from pip._internal.utils.deprecation import deprecated
from pip._internal.utils.logging import VERBOSE
from pip._internal.utils.packaging import get_requirement
from pip._internal.utils.subprocess import call_subprocess
from pip._internal.utils.temp_dir import TempDirectory, tempdir_kinds

Copy target:
imports/real_existing/azure/build_env.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/cli/autocompletion.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from __future__ import annotations
import optparse
import os
import sys
from collections.abc import Iterable
from itertools import chain
from typing import Any
from pip._internal.cli.main_parser import create_main_parser
from pip._internal.commands import commands_dict, create_command
from pip._internal.metadata import get_default_environment

Copy target:
imports/real_existing/azure/autocompletion.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/commands/check.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
import logging
from optparse import Values
from pip._internal.cli.base_command import Command
from pip._internal.cli.status_codes import ERROR, SUCCESS
from pip._internal.metadata import get_default_environment
from pip._internal.operations.check import (
from pip._internal.utils.compatibility_tags import get_supported
from pip._internal.utils.misc import write_output

Copy target:
imports/real_existing/azure/check.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/commands/debug.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from __future__ import annotations
import locale
import logging
import os
import sys
from optparse import Values
from types import ModuleType
from typing import Any
import pip._vendor
from pip._vendor.certifi import where
from pip._vendor.packaging.version import parse as parse_version
from pip._internal.cli import cmdoptions
from pip._internal.cli.base_command import Command
from pip._internal.cli.cmdoptions import make_target_python
from pip._internal.cli.status_codes import SUCCESS
from pip._internal.configuration import Configuration
from pip._internal.metadata import get_environment
from pip._internal.utils.compat import open_text_resource
from pip._internal.utils.logging import indent_log
from pip._internal.utils.misc import get_pip_version

Copy target:
imports/real_existing/azure/debug.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/commands/inspect.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
import logging
from optparse import Values
from typing import Any
from pip._vendor.packaging.markers import default_environment
from pip._vendor.rich import print_json
from pip import __version__
from pip._internal.cli import cmdoptions
from pip._internal.cli.base_command import Command
from pip._internal.cli.status_codes import SUCCESS
from pip._internal.metadata import BaseDistribution, get_environment
from pip._internal.utils.compat import stdlib_pkgs
from pip._internal.utils.urls import path_to_url

Copy target:
imports/real_existing/azure/inspect.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/commands/install.py

Purpose:
Matched real Aim2Build implementation for Azure.

Dependencies:
from __future__ import annotations
import errno
import json
import operator
import os
import shutil
import site
from optparse import SUPPRESS_HELP, Values
from pathlib import Path
from pip._vendor.packaging.utils import canonicalize_name
from pip._vendor.requests.exceptions import InvalidProxyURL
from pip._vendor.rich import print_json
import pip._internal.self_outdated_check  # noqa: F401
from pip._internal.cache import WheelCache
from pip._internal.cli import cmdoptions
from pip._internal.cli.cmdoptions import make_target_python
from pip._internal.cli.req_command import (
from pip._internal.cli.status_codes import ERROR, SUCCESS
from pip._internal.exceptions import (
from pip._internal.locations import get_scheme
from pip._internal.metadata import get_environment
from pip._internal.models.installation_report import InstallationReport
from pip._internal.operations.build.build_tracker import get_build_tracker
from pip._internal.operations.check import ConflictDetails, check_install_conflicts
from pip._internal.req import install_given_reqs
from pip._internal.req.req_install import (
from pip._internal.utils.compat import WINDOWS
from pip._internal.utils.filesystem import test_writable_dir
from pip._internal.utils.logging import getLogger
from pip._internal.utils.misc import (
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.utils.virtualenv import (
from pip._internal.wheel_builder import build

Copy target:
imports/real_existing/azure/install.py

CATEGORY: Image processing

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_subprocesses.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from __future__ import annotations
import sys
from collections.abc import AsyncIterable, Iterable, Mapping, Sequence
from io import BytesIO
from os import PathLike
from subprocess import PIPE, CalledProcessError, CompletedProcess
from typing import IO, Any, Union, cast
from ..abc import Process
from ._eventloop import get_async_backend
from ._tasks import create_task_group

Copy target:
imports/real_existing/image/_subprocesses.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_tempfile.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from __future__ import annotations
import os
import sys
import tempfile
from collections.abc import Iterable
from io import BytesIO, TextIOWrapper
from types import TracebackType
from typing import (
from .. import to_thread
from .._core._fileio import AsyncFile
from ..lowlevel import checkpoint_if_cancelled

Copy target:
imports/real_existing/image/_tempfile.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/click/_compat.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from __future__ import annotations
import codecs
import collections.abc as cabc
import io
import os
import re
import sys
import typing as t
from types import TracebackType
from weakref import WeakKeyDictionary

Copy target:
imports/real_existing/image/_compat.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/click/termui.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from __future__ import annotations
import collections.abc as cabc
import inspect
import io
import itertools
import sys
import typing as t
from contextlib import AbstractContextManager
from gettext import gettext as _
from ._compat import isatty
from ._compat import strip_ansi
from .exceptions import Abort
from .exceptions import UsageError
from .globals import resolve_color_default
from .types import Choice
from .types import convert_type
from .types import ParamType
from .utils import echo
from .utils import LazyFile

Copy target:
imports/real_existing/image/termui.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi-0.128.0.dist-info/RECORD

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:

Copy target:
imports/real_existing/image/RECORD

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi/__init__.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from starlette import status as status
from .applications import FastAPI as FastAPI
from .background import BackgroundTasks as BackgroundTasks
from .datastructures import UploadFile as UploadFile
from .exceptions import HTTPException as HTTPException
from .exceptions import WebSocketException as WebSocketException
from .param_functions import Body as Body
from .param_functions import Cookie as Cookie
from .param_functions import Depends as Depends
from .param_functions import File as File
from .param_functions import Form as Form
from .param_functions import Header as Header
from .param_functions import Path as Path
from .param_functions import Query as Query
from .param_functions import Security as Security
from .requests import Request as Request
from .responses import Response as Response
from .routing import APIRouter as APIRouter
from .websockets import WebSocket as WebSocket
from .websockets import WebSocketDisconnect as WebSocketDisconnect

Copy target:
imports/real_existing/image/__init__.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi/background.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from typing import Annotated, Any, Callable
from annotated_doc import Doc
from starlette.background import BackgroundTasks as StarletteBackgroundTasks
from typing_extensions import ParamSpec

Copy target:
imports/real_existing/image/background.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi/dependencies/models.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
import inspect
import sys
from dataclasses import dataclass, field
from functools import cached_property, partial
from typing import Any, Callable, Optional, Union
from fastapi._compat import ModelField
from fastapi.security.base import SecurityBase
from fastapi.types import DependencyCacheKey
from typing_extensions import Literal

Copy target:
imports/real_existing/image/models.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi/dependencies/utils.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
import dataclasses
import inspect
import sys
from collections.abc import Coroutine, Mapping, Sequence
from contextlib import AsyncExitStack, contextmanager
from copy import copy, deepcopy
from dataclasses import dataclass
from typing import (
import anyio
from fastapi import params
from fastapi._compat import (
from fastapi.background import BackgroundTasks
from fastapi.concurrency import (
from fastapi.dependencies.models import Dependant
from fastapi.exceptions import DependencyScopeError
from fastapi.logger import logger
from fastapi.security.oauth2 import SecurityScopes
from fastapi.types import DependencyCacheKey
from fastapi.utils import create_model_field, get_path_param_names
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from starlette.background import BackgroundTasks as StarletteBackgroundTasks
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import (
from starlette.requests import HTTPConnection, Request
from starlette.responses import Response
from starlette.websockets import WebSocket
from typing_extensions import Literal, get_args, get_origin

Copy target:
imports/real_existing/image/utils.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/fastapi/routing.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
import email.message
import functools
import inspect
import json
from collections.abc import (
from contextlib import AsyncExitStack, asynccontextmanager
from enum import Enum, IntEnum
from typing import (
from annotated_doc import Doc
from fastapi import params
from fastapi._compat import (
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.dependencies.models import Dependant
from fastapi.dependencies.utils import (
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import (
from fastapi.types import DecoratedCallable, IncEx
from fastapi.utils import (
from starlette import routing
from starlette._exception_handler import wrap_app_handling_exceptions
from starlette._utils import is_async_callable
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import (
from starlette.routing import Mount as Mount  # noqa
from starlette.types import AppType, ASGIApp, Lifespan, Receive, Scope, Send
from starlette.websockets import WebSocket
from typing_extensions import deprecated

Copy target:
imports/real_existing/image/routing.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/cli/spinners.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from __future__ import annotations
import contextlib
import itertools
import logging
import sys
import time
from collections.abc import Generator
from typing import IO, Final
from pip._vendor.rich.console import (
from pip._vendor.rich.live import Live
from pip._vendor.rich.measure import Measurement
from pip._vendor.rich.text import Text
from pip._internal.utils.compat import WINDOWS
from pip._internal.utils.logging import get_console, get_indentation

Copy target:
imports/real_existing/image/spinners.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/network/session.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from __future__ import annotations
import email.utils
import functools
import io
import ipaddress
import json
import logging
import mimetypes
import os
import platform
import shutil
import subprocess
import sys
import urllib.parse
import warnings
from collections.abc import Generator, Mapping, Sequence
from typing import (
from pip._vendor import requests, urllib3
from pip._vendor.cachecontrol import CacheControlAdapter as _BaseCacheControlAdapter
from pip._vendor.requests.adapters import DEFAULT_POOLBLOCK, BaseAdapter
from pip._vendor.requests.adapters import HTTPAdapter as _BaseHTTPAdapter
from pip._vendor.requests.models import PreparedRequest, Response
from pip._vendor.requests.structures import CaseInsensitiveDict
from pip._vendor.urllib3.connectionpool import ConnectionPool
from pip._vendor.urllib3.exceptions import InsecureRequestWarning
from pip import __version__
from pip._internal.metadata import get_default_environment
from pip._internal.models.link import Link
from pip._internal.network.auth import MultiDomainBasicAuth
from pip._internal.network.cache import SafeFileCache
from pip._internal.utils.compat import has_tls
from pip._internal.utils.glibc import libc_ver
from pip._internal.utils.misc import build_url_from_netloc, parse_netloc
from pip._internal.utils.urls import url_to_path

Copy target:
imports/real_existing/image/session.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/operations/install/wheel.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from __future__ import annotations
import collections
import compileall
import contextlib
import csv
import importlib
import logging
import os.path
import re
import shutil
import sys
import textwrap
import warnings
from base64 import urlsafe_b64encode
from collections.abc import Generator, Iterable, Iterator, Sequence
from email.message import Message
from itertools import chain, filterfalse, starmap
from typing import (
from zipfile import ZipFile, ZipInfo
from pip._vendor.distlib.scripts import ScriptMaker
from pip._vendor.distlib.util import get_export_entry
from pip._vendor.packaging.utils import canonicalize_name
from pip._internal.exceptions import InstallationError
from pip._internal.locations import get_major_minor_version
from pip._internal.metadata import (
from pip._internal.models.direct_url import DIRECT_URL_METADATA_NAME, DirectUrl
from pip._internal.models.scheme import SCHEME_KEYS, Scheme
from pip._internal.utils.filesystem import adjacent_tmp_file, replace
from pip._internal.utils.misc import StreamWrapper, ensure_dir, hash_file, partition
from pip._internal.utils.unpacking import (
from pip._internal.utils.wheel import parse_wheel

Copy target:
imports/real_existing/image/wheel.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/utils/logging.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from __future__ import annotations
import contextlib
import errno
import logging
import logging.handlers
import os
import sys
import threading
from collections.abc import Generator
from dataclasses import dataclass
from io import TextIOWrapper
from logging import Filter
from typing import Any, ClassVar
from pip._vendor.rich.console import (
from pip._vendor.rich.highlighter import NullHighlighter
from pip._vendor.rich.logging import RichHandler
from pip._vendor.rich.segment import Segment
from pip._vendor.rich.style import Style
from pip._internal.utils._log import VERBOSE, getLogger
from pip._internal.utils.compat import WINDOWS
from pip._internal.utils.deprecation import DEPRECATION_MSG_PREFIX
from pip._internal.utils.misc import ensure_dir

Copy target:
imports/real_existing/image/logging.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_internal/utils/unpacking.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from __future__ import annotations
import logging
import os
import shutil
import stat
import sys
import tarfile
import zipfile
from collections.abc import Iterable
from zipfile import ZipInfo
from pip._internal.exceptions import InstallationError
from pip._internal.utils.filetypes import (
from pip._internal.utils.misc import ensure_dir

Copy target:
imports/real_existing/image/unpacking.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_vendor/certifi/cacert.pem

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:

Copy target:
imports/real_existing/image/cacert.pem

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_vendor/distlib/util.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
import codecs
from collections import deque
import contextlib
import csv
from glob import iglob as std_iglob
import io
import json
import logging
import os
import py_compile
import re
import socket
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import time
from . import DistlibException
from .compat import (string_types, text_type, shutil, raw_input, StringIO, cache_from_source, urlopen, urljoin, httplib,

Copy target:
imports/real_existing/image/util.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_vendor/pygments/__init__.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
from io import StringIO, BytesIO

Copy target:
imports/real_existing/image/__init__.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_vendor/pygments/filters/__init__.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:
import re
from pip._vendor.pygments.token import String, Comment, Keyword, Name, Error, Whitespace, \
from pip._vendor.pygments.filter import Filter
from pip._vendor.pygments.util import get_list_opt, get_int_opt, get_bool_opt, \
from pip._vendor.pygments.plugin import find_plugin_filters

Copy target:
imports/real_existing/image/__init__.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_vendor/pygments/lexers/_mapping.py

Purpose:
Matched real Aim2Build implementation for Image processing.

Dependencies:

Copy target:
imports/real_existing/image/_mapping.py

CATEGORY: Worker framework

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.claude/settings.local.json

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:

Copy target:
imports/real_existing/workers/settings.local.json

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.idea/workspace.xml

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:

Copy target:
imports/real_existing/workers/workspace.xml

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/annotated_doc-0.0.4.dist-info/METADATA

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from typing import Annotated
from annotated_doc import Doc
from typing import Annotated
from annotated_doc import Doc

Copy target:
imports/real_existing/workers/METADATA

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio-4.12.0.dist-info/METADATA

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:

Copy target:
imports/real_existing/workers/METADATA

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio-4.12.0.dist-info/RECORD

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:

Copy target:
imports/real_existing/workers/RECORD

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/__init__.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
from ._core._contextmanagers import AsyncContextManagerMixin as AsyncContextManagerMixin
from ._core._contextmanagers import ContextManagerMixin as ContextManagerMixin
from ._core._eventloop import current_time as current_time
from ._core._eventloop import get_all_backends as get_all_backends
from ._core._eventloop import get_available_backends as get_available_backends
from ._core._eventloop import get_cancelled_exc_class as get_cancelled_exc_class
from ._core._eventloop import run as run
from ._core._eventloop import sleep as sleep
from ._core._eventloop import sleep_forever as sleep_forever
from ._core._eventloop import sleep_until as sleep_until
from ._core._exceptions import BrokenResourceError as BrokenResourceError
from ._core._exceptions import BrokenWorkerInterpreter as BrokenWorkerInterpreter
from ._core._exceptions import BrokenWorkerProcess as BrokenWorkerProcess
from ._core._exceptions import BusyResourceError as BusyResourceError
from ._core._exceptions import ClosedResourceError as ClosedResourceError
from ._core._exceptions import ConnectionFailed as ConnectionFailed
from ._core._exceptions import DelimiterNotFound as DelimiterNotFound
from ._core._exceptions import EndOfStream as EndOfStream
from ._core._exceptions import IncompleteRead as IncompleteRead
from ._core._exceptions import NoEventLoopError as NoEventLoopError
from ._core._exceptions import RunFinishedError as RunFinishedError
from ._core._exceptions import TypedAttributeLookupError as TypedAttributeLookupError
from ._core._exceptions import WouldBlock as WouldBlock
from ._core._fileio import AsyncFile as AsyncFile
from ._core._fileio import Path as Path
from ._core._fileio import open_file as open_file
from ._core._fileio import wrap_file as wrap_file
from ._core._resources import aclose_forcefully as aclose_forcefully
from ._core._signals import open_signal_receiver as open_signal_receiver
from ._core._sockets import TCPConnectable as TCPConnectable
from ._core._sockets import UNIXConnectable as UNIXConnectable
from ._core._sockets import as_connectable as as_connectable
from ._core._sockets import connect_tcp as connect_tcp
from ._core._sockets import connect_unix as connect_unix
from ._core._sockets import create_connected_udp_socket as create_connected_udp_socket
from ._core._sockets import (
from ._core._sockets import create_tcp_listener as create_tcp_listener
from ._core._sockets import create_udp_socket as create_udp_socket
from ._core._sockets import create_unix_datagram_socket as create_unix_datagram_socket

Copy target:
imports/real_existing/workers/__init__.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_backends/_asyncio.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import array
import asyncio
import concurrent.futures
import contextvars
import math
import os
import socket
import sys
import threading
import weakref
from asyncio import (
from asyncio.base_events import _run_until_complete_cb  # type: ignore[attr-defined]
from collections import OrderedDict, deque
from collections.abc import (
from concurrent.futures import Future
from contextlib import AbstractContextManager, suppress
from contextvars import Context, copy_context
from dataclasses import dataclass, field
from functools import partial, wraps
from inspect import (
from io import IOBase
from os import PathLike
from queue import Queue
from signal import Signals
from socket import AddressFamily, SocketKind
from threading import Thread
from types import CodeType, TracebackType
from typing import (
from weakref import WeakKeyDictionary
from .. import (
from .._core._eventloop import (
from .._core._exceptions import (
from .._core._sockets import convert_ipv6_sockaddr
from .._core._streams import create_memory_object_stream
from .._core._synchronization import (
from .._core._synchronization import Event as BaseEvent
from .._core._synchronization import Lock as BaseLock
from .._core._synchronization import (
from .._core._synchronization import Semaphore as BaseSemaphore

Copy target:
imports/real_existing/workers/_asyncio.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_backends/_trio.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import array
import math
import os
import socket
import sys
import types
import weakref
from collections.abc import (
from concurrent.futures import Future
from contextlib import AbstractContextManager
from dataclasses import dataclass
from functools import partial
from io import IOBase
from os import PathLike
from signal import Signals
from socket import AddressFamily, SocketKind
from types import TracebackType
from typing import (
import trio.from_thread
import trio.lowlevel
from outcome import Error, Outcome, Value
from trio.lowlevel import (
from trio.socket import SocketType as TrioSocketType
from trio.to_thread import run_sync
from .. import (
from .._core._eventloop import claim_worker_thread
from .._core._exceptions import (
from .._core._sockets import convert_ipv6_sockaddr
from .._core._streams import create_memory_object_stream
from .._core._synchronization import (
from .._core._synchronization import Event as BaseEvent
from .._core._synchronization import Lock as BaseLock
from .._core._synchronization import (
from .._core._synchronization import Semaphore as BaseSemaphore
from .._core._tasks import CancelScope as BaseCancelScope
from ..abc import IPSockAddrType, UDPPacketType, UNIXDatagramPacketType
from ..abc._eventloop import AsyncBackend, StrOrBytesPath
from ..streams.memory import MemoryObjectSendStream

Copy target:
imports/real_existing/workers/_trio.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_asyncio_selector_thread.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import asyncio
import socket
import threading
from collections.abc import Callable
from selectors import EVENT_READ, EVENT_WRITE, DefaultSelector
from typing import TYPE_CHECKING, Any

Copy target:
imports/real_existing/workers/_asyncio_selector_thread.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_eventloop.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import math
import sys
import threading
from collections.abc import Awaitable, Callable, Generator
from contextlib import contextmanager
from contextvars import Token
from importlib import import_module
from typing import TYPE_CHECKING, Any, TypeVar

Copy target:
imports/real_existing/workers/_eventloop.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_exceptions.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import sys
from collections.abc import Generator
from textwrap import dedent
from typing import Any

Copy target:
imports/real_existing/workers/_exceptions.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_resources.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
from ..abc import AsyncResource
from ._tasks import CancelScope

Copy target:
imports/real_existing/workers/_resources.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_sockets.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import errno
import os
import socket
import ssl
import stat
import sys
from collections.abc import Awaitable
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address, ip_address
from os import PathLike, chmod
from socket import AddressFamily, SocketKind
from typing import TYPE_CHECKING, Any, Literal, cast, overload
from .. import ConnectionFailed, to_thread
from ..abc import (
from ..streams.stapled import MultiListener
from ..streams.tls import TLSConnectable, TLSStream
from ._eventloop import get_async_backend
from ._resources import aclose_forcefully
from ._synchronization import Event
from ._tasks import create_task_group, move_on_after

Copy target:
imports/real_existing/workers/_sockets.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_subprocesses.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import sys
from collections.abc import AsyncIterable, Iterable, Mapping, Sequence
from io import BytesIO
from os import PathLike
from subprocess import PIPE, CalledProcessError, CompletedProcess
from typing import IO, Any, Union, cast
from ..abc import Process
from ._eventloop import get_async_backend
from ._tasks import create_task_group

Copy target:
imports/real_existing/workers/_subprocesses.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_synchronization.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import math
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import TypeVar
from ..lowlevel import checkpoint_if_cancelled
from ._eventloop import NoCurrentAsyncBackend, get_async_backend
from ._exceptions import BusyResourceError
from ._tasks import CancelScope
from ._testing import TaskInfo, get_current_task

Copy target:
imports/real_existing/workers/_synchronization.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_tasks.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import math
from collections.abc import Generator
from contextlib import contextmanager
from types import TracebackType
from ..abc._tasks import TaskGroup, TaskStatus
from ._eventloop import get_async_backend

Copy target:
imports/real_existing/workers/_tasks.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/_core/_testing.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
from collections.abc import Awaitable, Generator
from typing import Any, cast
from ._eventloop import get_async_backend

Copy target:
imports/real_existing/workers/_testing.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/abc/__init__.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
from ._eventloop import AsyncBackend as AsyncBackend
from ._resources import AsyncResource as AsyncResource
from ._sockets import ConnectedUDPSocket as ConnectedUDPSocket
from ._sockets import ConnectedUNIXDatagramSocket as ConnectedUNIXDatagramSocket
from ._sockets import IPAddressType as IPAddressType
from ._sockets import IPSockAddrType as IPSockAddrType
from ._sockets import SocketAttribute as SocketAttribute
from ._sockets import SocketListener as SocketListener
from ._sockets import SocketStream as SocketStream
from ._sockets import UDPPacketType as UDPPacketType
from ._sockets import UDPSocket as UDPSocket
from ._sockets import UNIXDatagramPacketType as UNIXDatagramPacketType
from ._sockets import UNIXDatagramSocket as UNIXDatagramSocket
from ._sockets import UNIXSocketStream as UNIXSocketStream
from ._streams import AnyByteReceiveStream as AnyByteReceiveStream
from ._streams import AnyByteSendStream as AnyByteSendStream
from ._streams import AnyByteStream as AnyByteStream
from ._streams import AnyByteStreamConnectable as AnyByteStreamConnectable
from ._streams import AnyUnreliableByteReceiveStream as AnyUnreliableByteReceiveStream
from ._streams import AnyUnreliableByteSendStream as AnyUnreliableByteSendStream
from ._streams import AnyUnreliableByteStream as AnyUnreliableByteStream
from ._streams import ByteReceiveStream as ByteReceiveStream
from ._streams import ByteSendStream as ByteSendStream
from ._streams import ByteStream as ByteStream
from ._streams import ByteStreamConnectable as ByteStreamConnectable
from ._streams import Listener as Listener
from ._streams import ObjectReceiveStream as ObjectReceiveStream
from ._streams import ObjectSendStream as ObjectSendStream
from ._streams import ObjectStream as ObjectStream
from ._streams import ObjectStreamConnectable as ObjectStreamConnectable
from ._streams import UnreliableObjectReceiveStream as UnreliableObjectReceiveStream
from ._streams import UnreliableObjectSendStream as UnreliableObjectSendStream
from ._streams import UnreliableObjectStream as UnreliableObjectStream
from ._subprocesses import Process as Process
from ._tasks import TaskGroup as TaskGroup
from ._tasks import TaskStatus as TaskStatus
from ._testing import TestRunner as TestRunner
from .._core._synchronization import (
from .._core._tasks import CancelScope as CancelScope

Copy target:
imports/real_existing/workers/__init__.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/abc/_eventloop.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import math
import sys
from abc import ABCMeta, abstractmethod
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import AbstractContextManager
from os import PathLike
from signal import Signals
from socket import AddressFamily, SocketKind, socket
from typing import (

Copy target:
imports/real_existing/workers/_eventloop.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/anyio/abc/_sockets.py

Purpose:
Matched real Aim2Build implementation for Worker framework.

Dependencies:
from __future__ import annotations
import errno
import socket
import sys
from abc import abstractmethod
from collections.abc import Callable, Collection, Mapping
from contextlib import AsyncExitStack
from io import IOBase
from ipaddress import IPv4Address, IPv6Address
from socket import AddressFamily
from typing import Any, TypeVar, Union
from .._core._eventloop import get_async_backend
from .._core._typedattr import (
from ._streams import ByteStream, Listener, UnreliableObjectStream
from ._tasks import TaskGroup

Copy target:
imports/real_existing/workers/_sockets.py

CATEGORY: Catalog access

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.gitignore

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/.gitignore

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.13/site-packages/pip/_vendor/pygments/lexers/_mapping.py

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/_mapping.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.9/site-packages/passlib/_data/wordsets/bip39.txt

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/bip39.txt

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.9/site-packages/passlib/_data/wordsets/eff_long.txt

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/eff_long.txt

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/.venv/lib/python3.9/site-packages/pip/_vendor/pygments/lexers/_mapping.py

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/_mapping.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/a2b_refresh_inventory_images.sh

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/a2b_refresh_inventory_images.sh

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/a2p_buildability_admin.sh

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/a2p_buildability_admin.sh

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/a2p_catalog_rebuild_contract.sh

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/a2p_catalog_rebuild_contract.sh

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/a2p_compare_local_vs_staging.sh

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/a2p_compare_local_vs_staging.sh

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/AIM2BUILD_FILTER_RUNBOOK.md

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/AIM2BUILD_FILTER_RUNBOOK.md

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/AIM2BUILD_LOCKED.md

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/AIM2BUILD_LOCKED.md

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/.venv/lib/python3.11/site-packages/passlib/_data/wordsets/bip39.txt

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/bip39.txt

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/.venv/lib/python3.11/site-packages/passlib/_data/wordsets/eff_long.txt

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/eff_long.txt

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/.venv/lib/python3.11/site-packages/pip/_vendor/chardet/metadata/languages.py

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:
from string import ascii_letters
from typing import List, Optional

Copy target:
imports/real_existing/catalog/languages.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/.venv/lib/python3.11/site-packages/pip/_vendor/pygments/lexers/_mapping.py

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/_mapping.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/.venv/lib/python3.11/site-packages/setuptools/config/_validate_pyproject/fastjsonschema_validations.py

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:
import re
from .fastjsonschema_exceptions import JsonSchemaValueException

Copy target:
imports/real_existing/catalog/fastjsonschema_validations.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/app/bricklink_mapping_db.py

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:
from __future__ import annotations
import json
import logging
import re
import sqlite3
from collections import deque
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.paths import DATA_DIR

Copy target:
imports/real_existing/catalog/bricklink_mapping_db.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/app/buy_sets_parts.py

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:
from __future__ import annotations
import logging
import sqlite3
from typing import Dict, List, Optional

Copy target:
imports/real_existing/catalog/buy_sets_parts.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/app/catalog_db.py

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:
from pathlib import Path
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import sqlite3
import os

Copy target:
imports/real_existing/catalog/catalog_db.py

Repo:
/Users/andrewcannell/aim2build-app-v2

File:
/Users/andrewcannell/aim2build-app-v2/backend/app/data/element_image_overrides.sql

Purpose:
Matched real Aim2Build implementation for Catalog access.

Dependencies:

Copy target:
imports/real_existing/catalog/element_image_overrides.sql
