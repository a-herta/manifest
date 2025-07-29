"""Main CLI entry point for Steam Manifest Tool."""

import subprocess
import sys
import time

from colorama import init

from ..core.client import SteamManifestClient
from ..utils.input_helper import custom_input
from ..utils.logger import setup_logger
from .args import parse_arguments
from .banner import show_banner

# Initialize colorama
init(autoreset=True)


def main():
    """Main entry point for the CLI application."""
    show_banner()

    try:
        # Parse command line arguments
        args = parse_arguments()

        # Set up logging
        logger = setup_logger(args.debug)

        # Get application ID
        app_id = args.appid or custom_input("Please enter game name/ID:")

        # Initialize client
        client = SteamManifestClient(
            api_token=args.key, repo=args.repo, fixed_mode=args.fixed, logger=logger
        )

        # Find application IDs
        try:
            app_ids = client.find_app_id(app_id)
        except Exception as e:
            logger.error(f"❌ Error searching for application: {str(e)}")
            time.sleep(1)
            sys.exit(1)

        # Process the application
        success = client.process_app(app_ids)

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

    # Pause if not called with appid argument (interactive mode)
    if not args.appid:
        time.sleep(0.1)
        subprocess.call("pause", shell=True)


if __name__ == "__main__":
    main()
