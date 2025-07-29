"""Input helper utilities for Steam Manifest Tool."""

from datetime import datetime

from colorama import Fore


def custom_input(prompt: str) -> str:
    """Custom input function with colored prompt and timestamp.

    Args:
        prompt: The input prompt message

    Returns:
        User input string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    formatted_prompt = f"{Fore.CYAN} {timestamp} [INPUT] {prompt}"
    return input(formatted_prompt)
