"""Main file for CLI."""

import sys
import argparse
from typing import List, Optional, Any

import shtab  # type: ignore

import altadb
from altadb.cli.command import (
    CLIConfigController,
    CLIUploadController,
    CLIListController,
    CLICreateController,
    CLIExportController,
    CLIQueryController,
)
from altadb.cli.cli_base import CLIInterface
from altadb.utils.logging import logger


class CLIController(CLIInterface):
    """Main CLI Controller."""

    def __init__(self, command: argparse._SubParsersAction) -> None:
        """Initialize CLI command parsers."""
        self.config = CLIConfigController(
            command.add_parser(
                self.CONFIG,
                help="Setup the credentials for your CLI.",
                description="Setup the credentials for your CLI.",
            )
        )
        self.upload = CLIUploadController(
            command.add_parser(
                self.UPLOAD,
                help="Upload files to a dataset",
                description="Upload files to a dataset",
            )
        )
        self.list = CLIListController(
            command.add_parser(
                self.LIST,
                help="List all datasets",
                description="List all datasets",
            )
        )
        self.create = CLICreateController(
            command.add_parser(
                self.CREATE,
                help="Create a dataset",
                description="Create a dataset",
            )
        )
        self.export = CLIExportController(
            command.add_parser(
                self.EXPORT,
                help="Export files from a dataset",
                description="Export files from a dataset",
            )
        )
        self.query = CLIQueryController(
            command.add_parser(
                self.QUERY,
                help="Query files from a dataset",
                description="Query files from a dataset",
            )
        )

    def handle_command(self, args: argparse.Namespace) -> None:
        """CLI command main handler."""
        if args.command == self.CONFIG:
            self.config.handler(args)
        elif args.command == self.UPLOAD:
            self.upload.handler(args)
        elif args.command == self.LIST:
            self.list.handler(args)
        elif args.command == self.QUERY:
            self.query.handler(args)
        elif args.command == self.CREATE:
            self.create.handler(args)
        elif args.command == self.EXPORT:
            self.export.handler(args)
        else:
            raise argparse.ArgumentError(None, "")


def cli_parser(
    only_parser: bool = True,
) -> Any:
    """Initialize argument parser."""
    parser = argparse.ArgumentParser(
        description="The AltaDB CLI offers a simple interface to quickly import and "
        + "export your images & annotations, and perform other high-level actions."
    )
    parser.add_argument("-v", "--version", action="version", version=altadb.version())
    cli = CLIController(parser.add_subparsers(title="Commands", dest="command"))

    shtab.add_argument_to(parser, "--completion")

    if only_parser:
        return parser

    return parser, cli


def cli_main(argv: Optional[List[str]] = None) -> None:
    """CLI main handler."""
    parser: argparse.ArgumentParser
    cli: CLIController

    parser, cli = cli_parser(False)

    try:
        args = parser.parse_args(argv if argv is not None else sys.argv[1:])
        logger.debug(args)
    except KeyboardInterrupt:
        logger.warning("User interrupted")
    except argparse.ArgumentError as error:
        logger.warning(str(error))
        parser.print_help()
    else:
        try:
            cli.handle_command(args)
        except KeyboardInterrupt:
            logger.warning("User interrupted")
        except argparse.ArgumentError as error:
            message = str(error)
            if message:
                logger.warning(message)

            if args.command:
                actions = (
                    parser._get_positional_actions()  # pylint: disable=protected-access
                )
                if actions:
                    choices = actions[0].choices
                    if choices:
                        subparser = dict(choices).get(args.command)
                        if subparser:
                            subparser.print_usage()
                            sys.exit(1)

            parser.print_usage()
            sys.exit(1)


if __name__ == "__main__":
    cli_main()
