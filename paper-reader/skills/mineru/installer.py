"""MinerU installer.

Handles installation of the MinerU PDF parser, including Python version
checks, user consent, platform-specific pip install, and post-install
verification.
"""

import logging
import subprocess
import sys
from shutil import which

from skills.config.config_manager import ConfigManager
from skills.config.platform import get_platform
from skills.mineru.detector import detect_mineru

logger = logging.getLogger(__name__)

MIN_PYTHON_VERSION = (3, 10)


def check_python_version() -> tuple[bool, str]:
    """Check whether the running Python meets the minimum version requirement.

    Returns:
        (ok, message) where *ok* is True when Python >= 3.10, and *message*
        is a human-readable description.
    """
    current = sys.version_info[:2]
    if current >= MIN_PYTHON_VERSION:
        return True, f"Python {current[0]}.{current[1]} meets requirement (>={MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]})"
    return False, f"Python {current[0]}.{current[1]} is too old; MinerU requires Python >={MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}"


def verify_installation() -> dict:
    """Run detection to confirm MinerU is installed.

    Returns:
        The detection result dict with keys ``installed``, ``path``, ``version``.
    """
    return detect_mineru()


def install_mineru(
    user_consent: bool,
    *,
    config_manager: ConfigManager | None = None,
    dry_run: bool = False,
) -> dict:
    """Install MinerU via pip.

    Args:
        user_consent: Must be True to proceed. If False, returns early with
            a message explaining that user confirmation is required.
        config_manager: Optional ConfigManager instance. If provided, the
            config will be updated with installation status after the
            install attempt. A fresh one is created if omitted.
        dry_run: If True, skip the actual pip install command (useful for
            testing). Verification still runs.

    Returns:
        dict with keys:
          - ``success`` (bool): whether installation succeeded
          - ``message`` (str): human-readable result description
          - ``detection`` (dict): result of :func:`verify_installation`
    """
    if not user_consent:
        return {
            "success": False,
            "message": "User confirmation is required before installing MinerU. Pass user_consent=True to proceed.",
            "detection": verify_installation(),
        }

    # Python version gate
    version_ok, version_msg = check_python_version()
    if not version_ok:
        raise RuntimeError(version_msg)

    # Determine pip command (prefer pip3, fall back to pip)
    pip_cmd = _resolve_pip_command()

    # Build the install command
    install_cmd = [pip_cmd, "install", "mineru"]

    logger.info("Installing MinerU: %s", " ".join(install_cmd))

    if not dry_run:
        try:
            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            msg = "pip install mineru timed out after 300 seconds"
            logger.error(msg)
            return {
                "success": False,
                "message": msg,
                "detection": verify_installation(),
            }
        except OSError as exc:
            msg = f"Failed to run pip install: {exc}"
            logger.error(msg)
            return {
                "success": False,
                "message": msg,
                "detection": verify_installation(),
            }

        if result.returncode != 0:
            stderr = result.stderr.strip()
            msg = f"pip install mineru failed (exit {result.returncode}): {stderr}"
            logger.error(msg)
            return {
                "success": False,
                "message": msg,
                "detection": verify_installation(),
            }

    # Verify installation
    detection = verify_installation()

    # Update config
    cfg = config_manager or ConfigManager()
    cfg.set("mineru.installed", detection["installed"])
    cfg.set("mineru.path", detection["path"])
    cfg.set("mineru.version", detection["version"])

    if detection["installed"]:
        message = "MinerU installed successfully"
        if dry_run:
            message = "MinerU installation skipped (dry_run=True)"
        logger.info(message)
    else:
        message = "MinerU pip install completed but verification could not find the installation"
        logger.warning(message)

    return {
        "success": detection["installed"],
        "message": message,
        "detection": detection,
    }


def _resolve_pip_command() -> str:
    """Return the pip command to use, preferring pip3 over pip.

    Returns:
        ``"pip3"`` if available on PATH, else ``"pip"``.
    """
    if which("pip3"):
        return "pip3"
    if which("pip"):
        return "pip"
    # Fallback — the install will likely fail, but let subprocess report it
    return "pip3"
