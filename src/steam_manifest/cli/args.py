"""Command line argument parsing for Steam Manifest Tool."""

from argparse import ArgumentParser, Namespace
from ..core.config import Config


def parse_arguments() -> Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = ArgumentParser(description="🚀 Steam Manifest File Fetching Tool")
    
    parser.add_argument(
        "-v", "--version", 
        action="version", 
        version=f"📦 %(prog)s v{Config.VERSION}"
    )
    
    parser.add_argument(
        "-a", "--appid", 
        help="🎮 Steam Application ID"
    )
    
    parser.add_argument(
        "-k", "--key", 
        help="🔑 GitHub API Access Token"
    )
    
    parser.add_argument(
        "-r", "--repo", 
        help="📁 GitHub Repository Name"
    )
    
    parser.add_argument(
        "-f", "--fixed", 
        action="store_true", 
        help="📌 Fixed Manifest Mode"
    )
    
    parser.add_argument(
        "-d", "--debug", 
        action="store_true", 
        help="🔍 Debug Mode"
    )
    
    return parser.parse_args()