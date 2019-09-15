import inspect
import sys
from abc import ABC, abstractmethod

import git
from cookiecutter.main import cookiecutter

from briefcase.config import AppConfig, GlobalConfig, parse_config
from briefcase.exceptions import BriefcaseConfigError


def create_config(klass, config, msg):
    try:
        return klass(**config)
    except TypeError:
        # Inspect the GlobalConfig constructor to find which
        # parameters are required and don't have a default
        # value.
        required_args = {
            name
            for name, param in inspect.signature(klass.__init__).parameters.items()
            if param.default == inspect._empty
            and name not in {'self', 'kwargs'}
        }
        missing_args = required_args - config.keys()
        missing = ', '.join(
            "'{arg}'".format(arg=arg)
            for arg in missing_args
        )
        raise BriefcaseConfigError(
            "{msg} is incomplete (missing {missing})".format(
                msg=msg,
                missing=missing
            )
        )


class BaseCommand(ABC):
    GLOBAL_CONFIG_CLASS = GlobalConfig
    APP_CONFIG_CLASS = AppConfig

    def __init__(self, platform, output_format, apps=None):
        self.platform = platform
        self.output_format = output_format
        self.options = None

        self.global_config = None
        self.apps = {} if apps is None else apps

        # External service APIs.
        # These are abstracted to enable testing without mocks.
        self.git = git
        self.cookiecutter = cookiecutter

    @abstractmethod
    def bundle_path(self, app, base_path):
        """
        The path to the bundle for the app in the output format.

        The bundle is the template-generated source form of the app.

        :param app: The app config
        :param base_path: The path to use as the root for all output
            (usually, the root of the project).
        """
        ...

    @abstractmethod
    def binary_path(self, app, base_path):
        """
        The path to the executable artefact for the app in the output format

        This *may* be the same as the bundle path, if the output format
        requires no compilation, or if it compiles in place.

        :param app: The app config
        :param base_path: The path to use as the root for all output
            (usually, the root of the project).
        """
        ...

    @property
    def python_version_tag(self):
        """
        The major.minor of the Python version in use, as a string.

        This is used as a repository label/tag to identify the appropriate
        templates, etc to use.
        """
        return '{major}.{minor}'.format(
            major=sys.version_info.major,
            minor=sys.version_info.minor
        )

    def parse_options(self, parser, extra):
        self.add_options(parser)

        # Parse the full set of command line options from the content
        # remaining after the basic command/platform/output format
        # has been extracted.
        self.options = parser.parse_args(extra)

    def add_options(self, parser):
        """
        Add any options that this command needs to parse from the command line.

        :param parser: a stub argparse parser for the command.
        """
        pass

    def parse_config(self, filename):
        try:
            with open(filename) as config_file:
                # Parse the content of the pyproject.toml file, extracting
                # any platform and output format configuration for each app,
                # creating a single set of configuration options.
                global_config, app_configs = parse_config(
                    config_file,
                    platform=self.platform,
                    output_format=self.output_format
                )

                self.global_config = create_config(
                    klass=self.GLOBAL_CONFIG_CLASS,
                    config=global_config,
                    msg="Global configuration"
                )

                for app_name, app_config in app_configs.items():
                    # Construct an AppConfig object with the final set of
                    # configuration options for the app.
                    self.apps[app_name] = create_config(
                        klass=self.APP_CONFIG_CLASS,
                        config=app_config,
                        msg="Configuration for '{app_name}'".format(
                            app_name=app_name
                        )
                    )

        except FileNotFoundError:
            raise BriefcaseConfigError('configuration file not found')
