#!/usr/bin/env python3

"""
============================================================
Tor / Kalitorify Setup + Automatic Rollback
============================================================

Purpose:
    Prepare a Linux system for Tor + Kalitorify.

Behavior:
    - Run as root.
    - Kalitorify is primarily intended for Kali Linux.
    - Automatically starts Kalitorify after setup.
    - Press Ctrl+C to stop Kalitorify and rollback changes.
    - Network interface is brought DOWN before restoration.
    - Original MAC address is restored while interface is DOWN.
    - Original hostname/timezone/Tor configuration are restored.
    - /etc/hosts is restored from backup.
    - Network interface is brought UP again afterward.
    - DHCP/NetworkManager reconnection is attempted.
    - Firewall is never automatically disabled.
    - Existing Tor settings are not blindly deleted.
    - No relay/country exclusion rules are configured.

Important:
    This does NOT guarantee anonymity.
    This does NOT guarantee a perfect system rollback.
    Packages installed by APT are intentionally NOT removed.
"""
import fcntl
import os
import platform
import shutil
import subprocess
import sys
import time

from datetime import datetime
from pathlib import Path
os.system("cls" if os.name == "nt" else "clear")
banner=r"""        
         _
 .---.  / > .---,
  <_  `'  `'  _>
    <_/\  /\_>
       /`'\
      ".__." 
Anonymity v1.1 (J4F)
"""
print(banner)
# ============================================================
# CONFIGURATION
# ============================================================

KALITORIFY_DIR = Path(
    "/opt/kalitorify"
)

KALITORIFY_REPO = (
    "https://github.com/brainfucksec/kalitorify.git"
)

HOSTNAME = "ubuntu-desktop"

TIMEZONE = "UTC"

# Set manually if required:
#
# INTERFACE = "eth0"
# INTERFACE = "wlan0"
#
# Leave as None for automatic detection.
INTERFACE = None

# Kalitorify is primarily designed for Kali Linux.
# Set True only if you intentionally want to run it
# on another Debian-based distribution.
ALLOW_UNSUPPORTED_DISTRO = False

# Never disable firewall automatically.
MANAGE_FIREWALL = False

# Change MAC automatically.
CHANGE_MAC = True

# Change hostname automatically.
CHANGE_HOSTNAME = True

# Change timezone automatically.
CHANGE_TIMEZONE = True

# Create anonymity shell alias.
CREATE_ALIAS = True

# Backups.
BACKUP_ROOT = Path(
    "/var/backups/tor-kalitorify"
)

# Prevent multiple instances.
LOCK_FILE = Path(
    "/run/lock/tor-kalitorify.lock"
)

# Default command timeout.
COMMAND_TIMEOUT = 300

# How often to show Kalitorify status
# while the program is running.
STATUS_INTERVAL = 30


# ============================================================
# OUTPUT COLORS
# ============================================================

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"


def info(message):
    print(
        f"{CYAN}[+]{RESET} {message}"
    )


def success(message):
    print(
        f"{GREEN}[OK]{RESET} {message}"
    )


def warning(message):
    print(
        f"{YELLOW}[!]{RESET} {message}"
    )


def error(message):
    print(
        f"{RED}[-]{RESET} {message}"
    )


# ============================================================
# GLOBAL ROLLBACK STATE
# ============================================================

INITIAL_STATE = {
    "interface": None,
    "original_mac": None,
    "hostname": None,
    "timezone": None,
    "tor_active": False,
    "tor_enabled": False,
    "network_was_up": False,
    "kalitorify_active": False,
}

SETUP_STARTED = False
CLEANUP_DONE = False
BACKUP_DIR = None


# ============================================================
# COMMAND HELPERS
# ============================================================

def run_command(
    command,
    check=True,
    timeout=COMMAND_TIMEOUT,
    cwd=None,
):
    """Execute a command safely."""

    try:

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=timeout,
            cwd=cwd,
        )

    except FileNotFoundError:

        error(
            f"Command not found: {command[0]}"
        )

        return None

    except subprocess.TimeoutExpired:

        error(
            f"Command timed out after "
            f"{timeout} seconds: "
            f"{' '.join(command)}"
        )

        return None

    except OSError as exc:

        error(
            f"Could not execute command "
            f"{' '.join(command)}: {exc}"
        )

        return None

    if check and result.returncode != 0:

        error(
            f"Command failed "
            f"({result.returncode}): "
            f"{' '.join(command)}"
        )

        if result.stderr.strip():

            print(
                result.stderr.strip()
            )

        return None

    return result


def command_exists(command):
    """Return True if command exists."""

    return shutil.which(command) is not None


def command_output(command):
    """Return stdout from successful command."""

    result = run_command(
        command
    )

    if result is None:
        return None

    return result.stdout.strip()


# ============================================================
# ROOT CHECK
# ============================================================

def check_root():
    """Require root privileges."""

    if os.geteuid() != 0:

        error(
            "This script requires root privileges."
        )

        print(
            "Run it with:"
        )

        print(
            f"    sudo python3 "
            f"{os.path.basename(sys.argv[0])}"
        )

        sys.exit(1)

    success(
        "Running with root privileges."
    )


# ============================================================
# SINGLE INSTANCE LOCK
# ============================================================

def acquire_lock():
    """Prevent multiple instances."""

    LOCK_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:

        handle = LOCK_FILE.open(
            "w"
        )

        fcntl.flock(
            handle.fileno(),
            fcntl.LOCK_EX | fcntl.LOCK_NB,
        )

        handle.write(
            str(os.getpid())
        )

        handle.flush()

        return handle

    except BlockingIOError:

        error(
            "Another instance is already running."
        )

        sys.exit(1)

    except OSError as exc:

        error(
            f"Could not acquire lock: {exc}"
        )

        sys.exit(1)


# ============================================================
# BACKUP SYSTEM
# ============================================================

def create_backup_directory():
    """Create timestamped backup directory."""

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_dir = (
        BACKUP_ROOT / timestamp
    )

    backup_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    return backup_dir


def backup_file(
    path,
    backup_dir,
):
    """Create a backup of a file."""

    path = Path(path)

    if not path.exists():
        return None

    destination = (
        backup_dir
        / path.as_posix().lstrip("/")
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        path,
        destination,
    )

    info(
        f"Backup created: {path}"
    )

    return destination


# ============================================================
# OPERATING SYSTEM
# ============================================================

def get_os_release():
    """Read /etc/os-release."""

    path = Path(
        "/etc/os-release"
    )

    if not path.exists():
        return {}

    values = {}

    try:

        for line in path.read_text(
            encoding="utf-8"
        ).splitlines():

            if "=" not in line:
                continue

            key, value = line.split(
                "=",
                1,
            )

            values[key] = value.strip(
                '"'
            )

    except OSError as exc:

        warning(
            f"Could not read /etc/os-release: {exc}"
        )

    return values


def check_operating_system():
    """Check Linux distribution."""

    if platform.system() != "Linux":

        error(
            "This script requires Linux."
        )

        return False

    os_release = get_os_release()

    distro_id = (
        os_release
        .get("ID", "")
        .lower()
    )

    distro_name = (
        os_release.get("PRETTY_NAME")
        or distro_id
        or "Unknown"
    )

    info(
        f"Detected operating system: "
        f"{distro_name}"
    )

    if distro_id == "kali":

        success(
            "Kali Linux detected."
        )

        return True

    if not ALLOW_UNSUPPORTED_DISTRO:

        error(
            "This system is not Kali Linux."
        )

        error(
            "Kalitorify is primarily designed "
            "for Kali Linux."
        )

        error(
            "Set ALLOW_UNSUPPORTED_DISTRO = True "
            "if you intentionally accept this."
        )

        return False

    warning(
        "Unsupported distribution override enabled."
    )

    return True


# ============================================================
# APT
# ============================================================

def check_apt():
    """Check for APT."""

    if not command_exists(
        "apt-get"
    ):

        error(
            "apt-get was not found."
        )

        return False

    success(
        "APT package manager detected."
    )

    return True


def apt_update():
    """Update APT metadata."""

    info(
        "Updating APT package information..."
    )

    result = run_command(
        [
            "apt-get",
            "update",
        ],
        timeout=600,
    )

    if result is None:
        return False

    success(
        "APT package information updated."
    )

    return True


def apt_install(packages):
    """Install missing packages."""

    if not packages:
        return True

    info(
        "Installing missing packages: "
        + ", ".join(packages)
    )

    result = run_command(
        [
            "apt-get",
            "install",
            "-y",
            *packages,
        ],
        timeout=900,
    )

    if result is None:
        return False

    success(
        "Required packages installed."
    )

    return True


# ============================================================
# DEPENDENCIES
# ============================================================

def check_dependencies():
    """Check and install dependencies."""

    info(
        "Checking required dependencies..."
    )

    package_map = {
        "git": "git",
        "make": "make",
        "ip": "iproute2",
        "macchanger": "macchanger",
        "tor": "tor",
        "curl": "curl",
        "systemctl": "systemd",
        "hostnamectl": "systemd",
    }

    # These are useful for network restoration,
    # but are not strictly required.
    optional_commands = {
        "nmcli": "network-manager",
        "dhclient": "isc-dhcp-client",
    }

    missing = []

    for command, package in package_map.items():

        if command_exists(command):

            success(
                f"{command}: available"
            )

        else:

            warning(
                f"{command}: missing"
            )

            missing.append(
                package
            )

    if missing:

        missing = sorted(
            set(missing)
        )

        if not check_apt():
            return False

        if not apt_update():
            return False

        if not apt_install(
            missing
        ):
            return False

    else:

        success(
            "All required dependencies "
            "are already installed."
        )

    # Optional network helpers.
    for command, package in (
        optional_commands.items()
    ):

        if command_exists(command):

            info(
                f"{command}: available"
            )

        else:

            warning(
                f"{command}: not available"
            )

    still_missing = [
        command
        for command in package_map
        if not command_exists(command)
    ]

    if still_missing:

        error(
            "Required commands still missing:"
        )

        for command in still_missing:

            print(
                f"    - {command}"
            )

        return False

    success(
        "All required dependencies are available."
    )

    return True


# ============================================================
# KALITORIFY
# ============================================================

def verify_git_repository():
    """Verify Kalitorify Git repository."""

    if not KALITORIFY_DIR.exists():
        return False

    git_dir = (
        KALITORIFY_DIR / ".git"
    )

    if not git_dir.exists():

        error(
            f"{KALITORIFY_DIR} exists but is not "
            "a Git repository."
        )

        return False

    result = run_command(
        [
            "git",
            "-C",
            str(KALITORIFY_DIR),
            "rev-parse",
            "--is-inside-work-tree",
        ],
        check=False,
    )

    if (
        result is None
        or result.returncode != 0
        or result.stdout.strip() != "true"
    ):

        error(
            "Git repository validation failed."
        )

        return False

    success(
        "Git repository validated."
    )

    return True


def clone_kalitorify():
    """Clone Kalitorify."""

    if KALITORIFY_DIR.exists():

        if verify_git_repository():
            return True

        error(
            "Refusing to delete the existing directory."
        )

        return False

    info(
        "Cloning Kalitorify repository..."
    )

    result = run_command(
        [
            "git",
            "clone",
            KALITORIFY_REPO,
            str(KALITORIFY_DIR),
        ],
        timeout=600,
    )

    if result is None:
        return False

    return verify_git_repository()


def verify_kalitorify():
    """Verify Kalitorify installation."""

    if not command_exists(
        "kalitorify"
    ):
        return False

    result = run_command(
        [
            "kalitorify",
            "--version",
        ],
        check=False,
    )

    if result is None:
        return False

    if result.returncode != 0:

        warning(
            "kalitorify exists but "
            "--version failed."
        )

        return False

    if result.stdout.strip():

        print(
            result.stdout.strip()
        )

    success(
        "Kalitorify command verified."
    )

    return True


def install_kalitorify():
    """Install Kalitorify if necessary."""

    info(
        "Checking Kalitorify installation..."
    )

    if command_exists(
        "kalitorify"
    ):

        if verify_kalitorify():

            success(
                "Kalitorify is already installed."
            )

            return True

    if not clone_kalitorify():
        return False

    info(
        "Installing Kalitorify..."
    )

    result = run_command(
        [
            "make",
            "install",
        ],
        cwd=str(KALITORIFY_DIR),
        timeout=600,
    )

    if result is None:
        return False

    if not verify_kalitorify():

        error(
            "Kalitorify installation verification failed."
        )

        return False

    success(
        "Kalitorify installed successfully."
    )

    return True


# ============================================================
# NETWORK INTERFACE
# ============================================================

def detect_interface():
    """Detect interface used by default route."""

    if INTERFACE:

        info(
            f"Using configured interface: "
            f"{INTERFACE}"
        )

        return INTERFACE

    info(
        "Detecting default network interface..."
    )

    result = run_command(
        [
            "ip",
            "-4",
            "route",
            "show",
            "default",
        ],
        check=False,
    )

    if result is None:
        return None

    for line in result.stdout.splitlines():

        parts = line.split()

        if "dev" not in parts:
            continue

        index = parts.index(
            "dev"
        )

        if index + 1 >= len(parts):
            continue

        interface = parts[
            index + 1
        ]

        if interface == "lo":
            continue

        success(
            f"Detected network interface: "
            f"{interface}"
        )

        return interface

    error(
        "Could not detect default network interface."
    )

    return None


def get_mac_address(interface):
    """Read current MAC address."""

    address_file = (
        Path("/sys/class/net")
        / interface
        / "address"
    )

    try:

        return address_file.read_text(
            encoding="utf-8"
        ).strip()

    except OSError:

        return None


def is_interface_up(interface):
    """Check whether interface is UP."""

    result = run_command(
        [
            "ip",
            "link",
            "show",
            "dev",
            interface,
        ],
        check=False,
    )

    if (
        result is None
        or result.returncode != 0
    ):

        return False

    output = result.stdout

    return (
        "state UP" in output
        or "<" in output
        and "UP" in output
    )


# ============================================================
# INITIAL STATE SNAPSHOT
# ============================================================

def snapshot_initial_state(interface):
    """Save system state before modifications."""

    INITIAL_STATE[
        "interface"
    ] = interface

    INITIAL_STATE[
        "original_mac"
    ] = get_mac_address(
        interface
    )

    INITIAL_STATE[
        "hostname"
    ] = command_output(
        ["hostname"]
    )

    INITIAL_STATE[
        "timezone"
    ] = command_output(
        [
            "timedatectl",
            "show",
            "--property=Timezone",
            "--value",
        ]
    )

    INITIAL_STATE[
        "network_was_up"
    ] = is_interface_up(
        interface
    )

    # Tor active state.
    tor_active = run_command(
        [
            "systemctl",
            "is-active",
            "--quiet",
            "tor",
        ],
        check=False,
    )

    INITIAL_STATE[
        "tor_active"
    ] = (
        tor_active is not None
        and tor_active.returncode == 0
    )

    # Tor enabled state.
    tor_enabled = run_command(
        [
            "systemctl",
            "is-enabled",
            "--quiet",
            "tor",
        ],
        check=False,
    )

    INITIAL_STATE[
        "tor_enabled"
    ] = (
        tor_enabled is not None
        and tor_enabled.returncode == 0
    )

    success(
        "Initial system state saved."
    )

    info(
        f"Interface: "
        f"{INITIAL_STATE['interface']}"
    )

    info(
        f"Original MAC: "
        f"{INITIAL_STATE['original_mac']}"
    )

    info(
        f"Original hostname: "
        f"{INITIAL_STATE['hostname']}"
    )

    info(
        f"Original timezone: "
        f"{INITIAL_STATE['timezone']}"
    )

    info(
        f"Network initially UP: "
        f"{INITIAL_STATE['network_was_up']}"
    )

    info(
        f"Tor initially active: "
        f"{INITIAL_STATE['tor_active']}"
    )

    info(
        f"Tor initially enabled: "
        f"{INITIAL_STATE['tor_enabled']}"
    )


# ============================================================
# NETWORK DOWN / UP
# ============================================================

def network_down(interface):
    """
    Bring network interface DOWN.

    This is intentionally done BEFORE rollback.
    """

    if not interface:
        return

    info(
        f"Bringing network interface DOWN: "
        f"{interface}"
    )

    result = run_command(
        [
            "ip",
            "link",
            "set",
            "dev",
            interface,
            "down",
        ],
        check=False,
    )

    if (
        result is None
        or result.returncode != 0
    ):

        warning(
            f"Could not bring {interface} down."
        )

        if (
            result
            and result.stderr.strip()
        ):

            print(
                result.stderr.strip()
            )

        return

    success(
        f"Network interface {interface} is DOWN."
    )


def restore_mac_after_network_down():
    """
    Restore original MAC.

    Interface MUST already be DOWN.
    """

    interface = INITIAL_STATE[
        "interface"
    ]

    original_mac = INITIAL_STATE[
        "original_mac"
    ]

    if not interface or not original_mac:

        warning(
            "Original MAC information unavailable."
        )

        return

    info(
        f"Restoring original MAC: "
        f"{original_mac}"
    )

    result = run_command(
        [
            "ip",
            "link",
            "set",
            "dev",
            interface,
            "address",
            original_mac,
        ],
        check=False,
    )

    if (
        result is None
        or result.returncode != 0
    ):

        warning(
            "Could not restore original MAC."
        )

        if (
            result
            and result.stderr.strip()
        ):

            print(
                result.stderr.strip()
            )

        return

    current_mac = get_mac_address(
        interface
    )

    if (
        current_mac
        and current_mac.lower()
        == original_mac.lower()
    ):

        success(
            f"MAC restored: {current_mac}"
        )

    else:

        warning(
            "MAC restoration could not be verified."
        )


def network_up():
    """Bring original interface UP."""

    interface = INITIAL_STATE[
        "interface"
    ]

    if not interface:
        return

    info(
        f"Bringing network interface UP: "
        f"{interface}"
    )

    result = run_command(
        [
            "ip",
            "link",
            "set",
            "dev",
            interface,
            "up",
        ],
        check=False,
    )

    if (
        result is None
        or result.returncode != 0
    ):

        warning(
            "Could not bring network interface up."
        )

        return

    success(
        f"Network interface {interface} is UP."
    )

    # NetworkManager.
    if command_exists(
        "nmcli"
    ):

        info(
            "Attempting NetworkManager reconnect..."
        )

        reconnect = run_command(
            [
                "nmcli",
                "device",
                "connect",
                interface,
            ],
            check=False,
            timeout=60,
        )

        if (
            reconnect is not None
            and reconnect.returncode == 0
        ):

            success(
                "NetworkManager connection restored."
            )

        return

    # DHCP fallback.
    if command_exists(
        "dhclient"
    ):

        info(
            "Attempting DHCP renewal..."
        )

        dhcp = run_command(
            [
                "dhclient",
                interface,
            ],
            check=False,
            timeout=60,
        )

        if (
            dhcp is not None
            and dhcp.returncode == 0
        ):

            success(
                "DHCP renewal completed."
            )


# ============================================================
# MAC ADDRESS
# ============================================================

def change_mac(interface):
    """Randomize MAC address."""

    interface_path = (
        Path("/sys/class/net")
        / interface
    )

    if not interface_path.exists():

        error(
            f"Interface does not exist: "
            f"{interface}"
        )

        return False

    original_mac = get_mac_address(
        interface
    )

    if not original_mac:

        error(
            "Could not determine original MAC."
        )

        return False

    info(
        f"Original MAC: {original_mac}"
    )

    down = run_command(
        [
            "ip",
            "link",
            "set",
            "dev",
            interface,
            "down",
        ]
    )

    if down is None:
        return False

    mac_result = run_command(
        [
            "macchanger",
            "-r",
            interface,
        ],
        check=False,
    )

    if (
        mac_result is None
        or mac_result.returncode != 0
    ):

        error(
            "macchanger failed."
        )

        if (
            mac_result
            and mac_result.stderr.strip()
        ):

            print(
                mac_result.stderr.strip()
            )

        # Restore while interface is still down.
        run_command(
            [
                "ip",
                "link",
                "set",
                "dev",
                interface,
                "address",
                original_mac,
            ],
            check=False,
        )

        run_command(
            [
                "ip",
                "link",
                "set",
                "dev",
                interface,
                "up",
            ],
            check=False,
        )

        return False

    up = run_command(
        [
            "ip",
            "link",
            "set",
            "dev",
            interface,
            "up",
        ]
    )

    if up is None:

        return False

    new_mac = get_mac_address(
        interface
    )

    if not new_mac:

        error(
            "Could not verify new MAC."
        )

        return False

    if (
        new_mac.lower()
        == original_mac.lower()
    ):

        warning(
            "MAC address did not change."
        )

        return False

    success(
        f"MAC changed: "
        f"{original_mac} -> {new_mac}"
    )

    return True


# ============================================================
# HOSTNAME
# ============================================================

def configure_hostname(
    backup_dir
):
    """Configure hostname safely."""

    current = command_output(
        ["hostname"]
    )

    if current == HOSTNAME:

        success(
            "Hostname is already configured."
        )

        return True

    hosts_file = Path(
        "/etc/hosts"
    )

    if hosts_file.exists():

        backup_file(
            hosts_file,
            backup_dir,
        )

    info(
        f"Setting hostname to {HOSTNAME}..."
    )

    result = run_command(
        [
            "hostnamectl",
            "set-hostname",
            HOSTNAME,
        ]
    )

    if result is None:
        return False

    try:

        lines = hosts_file.read_text(
            encoding="utf-8"
        ).splitlines()

        output = []
        found = False

        for line in lines:

            if line.strip().startswith(
                "127.0.1.1"
            ):

                output.append(
                    f"127.0.1.1\t{HOSTNAME}"
                )

                found = True

            else:

                output.append(line)

        if not found:

            output.append(
                f"127.0.1.1\t{HOSTNAME}"
            )

        hosts_file.write_text(
            "\n".join(output)
            + "\n",
            encoding="utf-8",
        )

    except OSError as exc:

        error(
            f"Could not update /etc/hosts: "
            f"{exc}"
        )

        return False

    verified = command_output(
        ["hostname"]
    )

    if verified != HOSTNAME:

        error(
            "Hostname verification failed."
        )

        return False

    success(
        "Hostname configured successfully."
    )

    return True


# ============================================================
# TIMEZONE
# ============================================================

def configure_timezone():
    """Configure timezone."""

    current = command_output(
        [
            "timedatectl",
            "show",
            "--property=Timezone",
            "--value",
        ]
    )

    if current == TIMEZONE:

        success(
            f"Timezone is already {TIMEZONE}."
        )

        return True

    info(
        f"Setting timezone to {TIMEZONE}..."
    )

    result = run_command(
        [
            "timedatectl",
            "set-timezone",
            TIMEZONE,
        ]
    )

    if result is None:
        return False

    verified = command_output(
        [
            "timedatectl",
            "show",
            "--property=Timezone",
            "--value",
        ]
    )

    if verified != TIMEZONE:

        error(
            "Timezone verification failed."
        )

        return False

    success(
        f"Timezone configured: {TIMEZONE}"
    )

    return True


# ============================================================
# TOR
# ============================================================

def configure_tor(
    backup_dir
):
    """
    Validate Tor configuration.

    Existing settings are NOT blindly deleted.
    """

    torrc = Path(
        "/etc/tor/torrc"
    )

    if not torrc.exists():

        error(
            "/etc/tor/torrc was not found."
        )

        return False

    backup_file(
        torrc,
        backup_dir,
    )

    info(
        "Validating Tor configuration..."
    )

    result = run_command(
        [
            "tor",
            "--verify-config",
            "-f",
            str(torrc),
        ],
        check=False,
    )

    if result is None:
        return False

    if result.returncode != 0:

        error(
            "Tor configuration validation failed."
        )

        if result.stderr.strip():

            print(
                result.stderr.strip()
            )

        return False

    success(
        "Tor configuration is valid."
    )

    return True


def start_tor():
    """Enable and restart Tor."""

    info(
        "Enabling Tor service..."
    )

    run_command(
        [
            "systemctl",
            "enable",
            "tor",
        ],
        check=False,
    )

    info(
        "Restarting Tor service..."
    )

    restart = run_command(
        [
            "systemctl",
            "restart",
            "tor",
        ],
        check=False,
    )

    if (
        restart is None
        or restart.returncode != 0
    ):

        error(
            "Failed to restart Tor."
        )

        if (
            restart
            and restart.stderr.strip()
        ):

            print(
                restart.stderr.strip()
            )

        return False

    active = run_command(
        [
            "systemctl",
            "is-active",
            "--quiet",
            "tor",
        ],
        check=False,
    )

    if (
        active is None
        or active.returncode != 0
    ):

        error(
            "Tor service is not active."
        )

        return False

    success(
        "Tor service is active."
    )

    return True


# ============================================================
# FIREWALL
# ============================================================

def configure_firewall():
    """Inspect firewall without disabling it."""

    if not command_exists(
        "ufw"
    ):

        info(
            "UFW is not installed."
        )

        return True

    info(
        "UFW detected."
    )

    info(
        "Firewall will NOT be disabled automatically."
    )

    run_command(
        [
            "ufw",
            "status",
        ],
        check=False,
    )

    return True


# ============================================================
# ALIAS
# ============================================================

def setup_alias(
    backup_dir
):
    """Create system-wide anonymity alias."""

    script_path = Path(
        os.path.abspath(
            sys.argv[0]
        )
    )

    alias_line = (
        f"\nalias anonymity='sudo python3 "
        f"\"{script_path}\"'\n"
    )

    rc_files = [
        Path("/etc/bash.bashrc"),
        Path("/etc/zsh/zshrc"),
    ]

    for rc_file in rc_files:

        if not rc_file.exists():
            continue

        try:

            content = rc_file.read_text(
                encoding="utf-8"
            )

        except OSError as exc:

            warning(
                f"Could not read "
                f"{rc_file}: {exc}"
            )

            continue

        if "alias anonymity=" in content:

            info(
                f"Alias already exists "
                f"in {rc_file}."
            )

            continue

        backup_file(
            rc_file,
            backup_dir,
        )

        try:

            with rc_file.open(
                "a",
                encoding="utf-8",
            ) as file:

                file.write(
                    alias_line
                )

        except OSError as exc:

            warning(
                f"Could not modify "
                f"{rc_file}: {exc}"
            )

            continue

        success(
            f"Added 'anonymity' alias "
            f"to {rc_file}."
        )


# ============================================================
# KALITORIFY START / STOP
# ============================================================

def start_kalitorify():
    """Start Kalitorify."""

    if not verify_kalitorify():

        error(
            "Kalitorify verification failed."
        )

        return False

    info(
        "Checking current Kalitorify status..."
    )

    run_command(
        [
            "kalitorify",
            "--status",
        ],
        check=False,
    )

    info(
        "Starting Kalitorify..."
    )

    result = run_command(
        [
            "kalitorify",
            "--tor",
        ],
        check=False,
        timeout=300,
    )

    if result is None:
        return False

    if result.returncode != 0:

        error(
            "Kalitorify failed to start."
        )

        if result.stderr.strip():

            print(
                result.stderr.strip()
            )

        return False

    INITIAL_STATE[
        "kalitorify_active"
    ] = True

    success(
        "Kalitorify started successfully."
    )

    return True


def stop_kalitorify():
    """Stop Kalitorify."""

    if not command_exists(
        "kalitorify"
    ):

        return

    info(
        "Stopping Kalitorify..."
    )

    result = run_command(
        [
            "kalitorify",
            "--stop",
        ],
        check=False,
        timeout=300,
    )

    if (
        result is not None
        and result.returncode == 0
    ):

        success(
            "Kalitorify stopped."
        )

    else:

        warning(
            "Kalitorify stop returned an error."
        )

        if (
            result
            and result.stderr.strip()
        ):

            print(
                result.stderr.strip()
            )


# ============================================================
# STATUS
# ============================================================

def show_status():
    """Show Kalitorify status."""

    if not command_exists(
        "kalitorify"
    ):
        return

    info(
        "Checking Kalitorify status..."
    )

    run_command(
        [
            "kalitorify",
            "--status",
        ],
        check=False,
    )


def show_ip_info():
    """Show public IP information."""

    if not command_exists(
        "kalitorify"
    ):
        return

    info(
        "Checking public IP information..."
    )

    run_command(
        [
            "kalitorify",
            "--ipinfo",
        ],
        check=False,
        timeout=120,
    )


# ============================================================
# RESTORE HOSTNAME
# ============================================================

def restore_hostname():
    """Restore original hostname."""

    original = INITIAL_STATE[
        "hostname"
    ]

    if not original:
        return

    current = command_output(
        ["hostname"]
    )

    if current == original:

        success(
            "Hostname already matches original state."
        )

        return

    info(
        f"Restoring hostname: {original}"
    )

    result = run_command(
        [
            "hostnamectl",
            "set-hostname",
            original,
        ],
        check=False,
    )

    if (
        result is None
        or result.returncode != 0
    ):

        warning(
            "Could not restore hostname."
        )

        return

    success(
        "Hostname restored."
    )


# ============================================================
# RESTORE /etc/hosts
# ============================================================

def restore_hosts(
    backup_dir
):
    """Restore /etc/hosts."""

    if not backup_dir:
        return

    hosts_file = Path(
        "/etc/hosts"
    )

    backup_path = (
        backup_dir
        / "etc/hosts"
    )

    if not backup_path.exists():

        info(
            "No /etc/hosts backup found."
        )

        return

    info(
        "Restoring /etc/hosts..."
    )

    try:

        shutil.copy2(
            backup_path,
            hosts_file,
        )

        success(
            "/etc/hosts restored."
        )

    except OSError as exc:

        warning(
            f"Could not restore /etc/hosts: "
            f"{exc}"
        )


# ============================================================
# RESTORE TIMEZONE
# ============================================================

def restore_timezone():
    """Restore original timezone."""

    original = INITIAL_STATE[
        "timezone"
    ]

    if not original:
        return

    current = command_output(
        [
            "timedatectl",
            "show",
            "--property=Timezone",
            "--value",
        ]
    )

    if current == original:

        success(
            "Timezone already matches original state."
        )

        return

    info(
        f"Restoring timezone: {original}"
    )

    result = run_command(
        [
            "timedatectl",
            "set-timezone",
            original,
        ],
        check=False,
    )

    if (
        result is None
        or result.returncode != 0
    ):

        warning(
            "Could not restore timezone."
        )

        return

    success(
        "Timezone restored."
    )


# ============================================================
# RESTORE TOR
# ============================================================

def restore_tor(
    backup_dir
):
    """Restore original Tor configuration/state."""

    torrc = Path(
        "/etc/tor/torrc"
    )

    backup_path = (
        backup_dir
        / "etc/tor/torrc"
    )

    info(
        "Stopping Tor before restoration..."
    )

    run_command(
        [
            "systemctl",
            "stop",
            "tor",
        ],
        check=False,
    )

    if backup_path.exists():

        info(
            "Restoring original torrc..."
        )

        try:

            shutil.copy2(
                backup_path,
                torrc,
            )

            success(
                "Original torrc restored."
            )

        except OSError as exc:

            warning(
                f"Could not restore torrc: "
                f"{exc}"
            )

    # Restore original enabled state.
    if INITIAL_STATE[
        "tor_enabled"
    ]:

        run_command(
            [
                "systemctl",
                "enable",
                "tor",
            ],
            check=False,
        )

    else:

        run_command(
            [
                "systemctl",
                "disable",
                "tor",
            ],
            check=False,
        )

    # Restore original active state.
    if INITIAL_STATE[
        "tor_active"
    ]:

        info(
            "Tor was active before setup."
        )

        run_command(
            [
                "systemctl",
                "start",
                "tor",
            ],
            check=False,
        )

        success(
            "Tor service restored to active state."
        )

    else:

        info(
            "Tor was inactive before setup."
        )

        run_command(
            [
                "systemctl",
                "stop",
                "tor",
            ],
            check=False,
        )

        success(
            "Tor service restored to inactive state."
        )


# ============================================================
# COMPLETE ROLLBACK
# ============================================================

def cleanup(
    backup_dir=None
):
    """
    Complete rollback.

    Order:

        1. Stop Kalitorify
        2. Network DOWN
        3. Restore MAC
        4. Restore Tor
        5. Restore hostname
        6. Restore /etc/hosts
        7. Restore timezone
        8. Network UP
        9. DHCP / NetworkManager reconnect
    """

    global CLEANUP_DONE

    if CLEANUP_DONE:
        return

    CLEANUP_DONE = True

    print()
    print(
        "============================================================"
    )
    print(
        " Starting rollback / cleanup"
    )
    print(
        "============================================================"
    )

    warning(
        "Restoring system state..."
    )

    interface = INITIAL_STATE[
        "interface"
    ]

    # --------------------------------------------------------
    # 1. STOP KALITORIFY
    # --------------------------------------------------------

    try:

        stop_kalitorify()

    except Exception as exc:

        warning(
            f"Kalitorify cleanup failed: {exc}"
        )

    # --------------------------------------------------------
    # 2. NETWORK DOWN FIRST
    # --------------------------------------------------------

    try:

        network_down(
            interface
        )

    except Exception as exc:

        warning(
            f"Network shutdown failed: {exc}"
        )

    # --------------------------------------------------------
    # 3. RESTORE MAC
    # --------------------------------------------------------

    try:

        restore_mac_after_network_down()

    except Exception as exc:

        warning(
            f"MAC restoration failed: {exc}"
        )

    # --------------------------------------------------------
    # 4. RESTORE TOR
    # --------------------------------------------------------

    if backup_dir:

        try:

            restore_tor(
                backup_dir
            )

        except Exception as exc:

            warning(
                f"Tor restoration failed: {exc}"
            )

    # --------------------------------------------------------
    # 5. RESTORE HOSTNAME
    # --------------------------------------------------------

    try:

        restore_hostname()

    except Exception as exc:

        warning(
            f"Hostname restoration failed: {exc}"
        )

    # --------------------------------------------------------
    # 6. RESTORE /etc/hosts
    # --------------------------------------------------------

    if backup_dir:

        try:

            restore_hosts(
                backup_dir
            )

        except Exception as exc:

            warning(
                f"/etc/hosts restoration failed: {exc}"
            )

    # --------------------------------------------------------
    # 7. RESTORE TIMEZONE
    # --------------------------------------------------------

    try:

        restore_timezone()

    except Exception as exc:

        warning(
            f"Timezone restoration failed: {exc}"
        )

    # --------------------------------------------------------
    # 8. NETWORK UP
    # --------------------------------------------------------

    if INITIAL_STATE[
        "network_was_up"
    ]:

        try:

            network_up()

        except Exception as exc:

            warning(
                f"Network restoration failed: {exc}"
            )

    else:

        info(
            "Network was originally DOWN; "
            "leaving it DOWN."
        )

    print()
    print(
        "============================================================"
    )

    success(
        "Rollback completed."
    )

    warning(
        "Installed packages and the Kalitorify repository "
        "were intentionally not removed."
    )

    warning(
        "This script cannot guarantee a perfect "
        "zero-trace rollback."
    )

    print(
        "============================================================"
    )


# ============================================================
# PREFLIGHT
# ============================================================

def preflight():
    """Perform checks before modifications."""

    info(
        "Running preflight checks..."
    )

    if not check_operating_system():
        return False

    if not check_apt():
        return False

    success(
        "Preflight checks passed."
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    global SETUP_STARTED
    global BACKUP_DIR

    print(
        "============================================================"
    )

    print(
        " Tor / Kalitorify Setup"
    )

    print(
        "============================================================"
    )

    print(
        "[*] Dependency pre-check: ENABLED"
    )

    print(
        "[*] Backup before changes: ENABLED"
    )

    print(
        "[*] Post-install verification: ENABLED"
    )

    print(
        "[*] Automatic firewall disabling: DISABLED"
    )

    print(
        "[*] Relay/country exclusion: NOT CONFIGURED"
    )

    print(
        "[*] Automatic Kalitorify start: ENABLED"
    )

    print(
        "[*] Ctrl+C rollback: ENABLED"
    )

    print(
        "[*] Network DOWN before restore: ENABLED"
    )

    print(
        "============================================================"
    )

    # --------------------------------------------------------
    # ROOT
    # --------------------------------------------------------

    check_root()

    # --------------------------------------------------------
    # LOCK
    # --------------------------------------------------------

    lock_handle = acquire_lock()

    # Keep file descriptor alive.
    _ = lock_handle

    # --------------------------------------------------------
    # PREFLIGHT
    # --------------------------------------------------------

    if not preflight():

        error(
            "Preflight checks failed."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # BACKUP DIRECTORY
    # --------------------------------------------------------

    try:

        BACKUP_DIR = (
            create_backup_directory()
        )

    except OSError as exc:

        error(
            f"Could not create backup directory: "
            f"{exc}"
        )

        sys.exit(1)

    success(
        f"Backup directory: {BACKUP_DIR}"
    )

    try:

        # ----------------------------------------------------
        # DEPENDENCIES
        # ----------------------------------------------------

        if not check_dependencies():

            raise RuntimeError(
                "Dependency setup failed."
            )

        # ----------------------------------------------------
        # KALITORIFY
        # ----------------------------------------------------

        if not install_kalitorify():

            raise RuntimeError(
                "Kalitorify installation failed."
            )

        # ----------------------------------------------------
        # INTERFACE
        # ----------------------------------------------------

        interface = detect_interface()

        if not interface:

            raise RuntimeError(
                "No usable network interface was detected."
            )

        # ----------------------------------------------------
        # SNAPSHOT BEFORE CHANGES
        # ----------------------------------------------------

        snapshot_initial_state(
            interface
        )

        SETUP_STARTED = True

        # ----------------------------------------------------
        # MAC
        # ----------------------------------------------------

        if CHANGE_MAC:

            if not change_mac(
                interface
            ):

                raise RuntimeError(
                    "MAC address configuration failed."
                )

        else:

            info(
                "MAC address change disabled."
            )

        # ----------------------------------------------------
        # HOSTNAME
        # ----------------------------------------------------

        if CHANGE_HOSTNAME:

            if not configure_hostname(
                BACKUP_DIR
            ):

                raise RuntimeError(
                    "Hostname configuration failed."
                )

        else:

            info(
                "Hostname configuration disabled."
            )

        # ----------------------------------------------------
        # TIMEZONE
        # ----------------------------------------------------

        if CHANGE_TIMEZONE:

            if not configure_timezone():

                raise RuntimeError(
                    "Timezone configuration failed."
                )

        else:

            info(
                "Timezone configuration disabled."
            )

        # ----------------------------------------------------
        # TOR CONFIGURATION
        # ----------------------------------------------------

        if not configure_tor(
            BACKUP_DIR
        ):

            raise RuntimeError(
                "Tor configuration validation failed."
            )

        # ----------------------------------------------------
        # TOR SERVICE
        # ----------------------------------------------------

        if not start_tor():

            raise RuntimeError(
                "Tor service could not be started."
            )

        # ----------------------------------------------------
        # FIREWALL
        # ----------------------------------------------------

        configure_firewall()

        # ----------------------------------------------------
        # ALIAS
        # ----------------------------------------------------

        if CREATE_ALIAS:

            setup_alias(
                BACKUP_DIR
            )

        else:

            info(
                "Alias creation disabled."
            )

        # ----------------------------------------------------
        # START KALITORIFY
        # ----------------------------------------------------

        info(
            "Starting Kalitorify automatically..."
        )

        if not start_kalitorify():

            raise RuntimeError(
                "Kalitorify activation failed."
            )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        show_status()

        show_ip_info()

        # ----------------------------------------------------
        # COMPLETE
        # ----------------------------------------------------

        print()
        print(
            "============================================================"
        )

        success(
            "Setup completed successfully."
        )

        success(
            "Tor service is active."
        )

        success(
            "Kalitorify is running."
        )

        success(
            "Press Ctrl+C to stop and rollback."
        )

        success(
            f"Backups: {BACKUP_DIR}"
        )

        warning(
            "This does NOT guarantee anonymity."
        )

        print(
            "============================================================"
        )

        # ----------------------------------------------------
        # KEEP PROCESS ALIVE
        # ----------------------------------------------------

        while True:

            time.sleep(
                STATUS_INTERVAL
            )

            show_status()

    except KeyboardInterrupt:

        print()

        warning(
            "Ctrl+C detected."
        )

        # finally below performs rollback.
        raise

    except Exception as exc:

        error(
            "Setup failed."
        )

        error(
            f"{type(exc).__name__}: {exc}"
        )

        # finally below performs rollback.
        raise

    finally:

        if SETUP_STARTED:

            cleanup(
                BACKUP_DIR
            )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()

        error(
            "Operation cancelled by user."
        )

        sys.exit(130)

    except Exception as exc:

        print()

        error(
            "Unexpected error:"
        )

        error(
            f"{type(exc).__name__}: {exc}"
        )

        sys.exit(1)