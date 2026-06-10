#  When running under Wayland, check if running under a supported
#  desktop environment and that the prereqs that desktop environment needs are
#  in place.
#
#  Supported compositors:
#    - GNOME (full support via the AutoKey GNOME Shell extension + uinput)
#    - KDE/KWin, Sway, Hyprland (partial: text expansion + hotkeys via
#      uinput; window title/class filtering not available yet)
#  Unsupported compositors emit a clear warning but do NOT abort startup so
#  that basic functionality remains usable on any Wayland session.

import getpass
import grp
import os
import subprocess

try:
    logger = __import__("autokey.logger").logger.get_logger(__name__)
except Exception:
    #  For standalone testing
    import logging
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Compositor identification helpers
# ---------------------------------------------------------------------------

def _detect_compositor():
    """
    Return a lowercase string identifying the active compositor.
    Returns one of: 'gnome', 'kde', 'sway', 'hyprland', 'unknown'.
    """
    desktop = (
        os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        or os.environ.get("DESKTOP_SESSION", "").lower()
    )
    session_desktop = os.environ.get("XDG_SESSION_DESKTOP", "").lower()

    if (
        "gnome" in desktop
        or "gnome" in session_desktop
        or "GNOME_DESKTOP_SESSION_ID" in os.environ
    ):
        return "gnome"
    if "kde" in desktop or "plasma" in desktop or "kde" in session_desktop:
        return "kde"
    if "sway" in desktop or "sway" in session_desktop or "SWAYSOCK" in os.environ:
        return "sway"
    if (
        "hyprland" in desktop
        or "hyprland" in session_desktop
        or "HYPRLAND_INSTANCE_SIGNATURE" in os.environ
    ):
        return "hyprland"

    # Process inspection fallback
    for proc, name in [
        ("gnome-shell", "gnome"),
        ("kwin_wayland", "kde"),
        ("sway", "sway"),
        ("Hyprland", "hyprland"),
    ]:
        try:
            r = subprocess.run(["pgrep", "-x", proc], capture_output=True, timeout=2)
            if r.returncode == 0:
                return name
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return "unknown"


# ---------------------------------------------------------------------------
# uinput / input-group checks (required for all Wayland compositors)
# ---------------------------------------------------------------------------

def _check_uinput_prerequisites():
    """
    Check that the user is in the 'input' group and has write access to
    /dev/uinput.  Returns (ok: bool, message: str).
    """
    group = "input"
    user = getpass.getuser()
    issues = []

    try:
        input_group = grp.getgrnam(group)
    except KeyError:
        issues.append(f'The "{group}" user group does not exist on this system.')
    else:
        if user not in input_group.gr_mem and os.geteuid() != 0:
            issues.append(
                f'User "{user}" is not in the "{group}" group.  '
                f'Run: sudo usermod -a -G {group} {user}  (then reboot)'
            )

    if not os.access("/dev/uinput", os.W_OK):
        issues.append(
            'No write access to /dev/uinput.  '
            'Add yourself to the "input" group and reboot, or run: '
            'sudo chmod a+rw /dev/uinput  (temporary fix).'
        )

    if issues:
        return False, "\n".join(issues)
    return True, ""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def waylandChecks():
    """
    Perform Wayland pre-flight checks.

    * On X11 sessions: always returns ``True`` immediately.
    * On Wayland + GNOME: full checks (extension present, input group, uinput).
    * On Wayland + KDE / Sway / Hyprland: uinput group check only; shows an
      informational warning about limited window-filtering support but still
      returns ``True`` so AutoKey can start.
    * On Wayland + unknown compositor: logs a warning and returns ``True``
      (best-effort mode).

    :returns: ``True`` if AutoKey should continue starting; ``False`` if a
              critical prerequisite is missing and the user has been informed.
    """
    try:
        if os.environ.get("XDG_SESSION_TYPE") != "wayland":
            return True

        compositor = _detect_compositor()
        logger.info(f"waylandChecks(): detected Wayland compositor: {compositor}")

        if compositor == "gnome":
            return _gnome_checks()
        elif compositor in ("kde", "sway", "hyprland"):
            return _partial_wayland_checks(compositor)
        else:
            return _unknown_compositor_checks()

    except Exception as e:
        logger.exception("Unexpected exception in waylandChecks()")
        return False


# ---------------------------------------------------------------------------
# Compositor-specific check functions
# ---------------------------------------------------------------------------

def _gnome_checks():
    """Full checks for GNOME/Wayland."""
    show_popup = False
    group = "input"
    user = getpass.getuser()

    # Check: AutoKey GNOME Shell extension
    ext_id = "autokey-gnome-extension@autokey"
    try:
        proc = subprocess.run(
            f"gnome-extensions info {ext_id}",
            shell=True, capture_output=True, check=True,
        )
        if "Enabled: Yes" in proc.stdout.decode("utf-8"):
            logger.debug("waylandChecks(): AutoKey GNOME Shell extension is enabled.")
        else:
            logger.debug(
                "waylandChecks(): AutoKey GNOME Shell extension found but disabled. "
                "Attempting to enable it."
            )
            subprocess.run(
                f"gnome-extensions enable {ext_id}",
                shell=True, capture_output=True, check=True,
            )
    except Exception:
        logger.critical("waylandChecks(): AutoKey GNOME Shell extension not found.")
        show_popup = True

    # Check: input group + uinput device
    ok, msg = _check_uinput_prerequisites()
    if not ok:
        logger.critical(f"waylandChecks(): uinput prerequisites not met: {msg}")
        show_popup = True

    if show_popup:
        title = "AutoKey System Configuration Needed"
        message = (
            f'Your system is not configured to run AutoKey under GNOME/Wayland.  '
            f'If this is your <b>first time</b> running AutoKey, try <b>rebooting</b> '
            f'and starting AutoKey again.  Otherwise, run these commands and reboot:<br /><br />'
            f'sudo usermod -a -G "{group}" "{user}"<br /><br />'
            f'gnome-extensions install --force '
            f'/usr/share/autokey/gnome-shell-extension/'
            f'autokey-gnome-extension@autokey.shell-extension.zip'
        )
        __show_popup(title, message)
        return False

    return True


def _partial_wayland_checks(compositor):
    """
    Checks for Wayland compositors with partial support (KDE, Sway, Hyprland).

    Text expansion and global hotkeys work via uinput.  Window title/class
    filtering is not available yet.  We warn the user but do NOT abort startup.
    """
    compositor_names = {
        "kde": "KDE Plasma / KWin",
        "sway": "Sway",
        "hyprland": "Hyprland",
    }
    display_name = compositor_names.get(compositor, compositor.upper())

    logger.warning(
        f"waylandChecks(): {display_name} Wayland detected.  "
        "Text expansion and hotkeys are functional via uinput.  "
        "Window title/class filtering is not yet supported on this compositor.  "
        "For full support see: https://github.com/autokey/autokey/issues/87"
    )

    # Still need uinput access for key injection
    ok, msg = _check_uinput_prerequisites()
    if not ok:
        logger.critical(
            f"waylandChecks(): uinput prerequisites not met on {display_name}: {msg}"
        )
        title = f"AutoKey — {display_name} Wayland: Configuration Needed"
        message = (
            f"AutoKey requires access to <b>/dev/uinput</b> for keyboard input on "
            f"Wayland.  {msg.replace(chr(10), '<br />')}<br /><br />"
            "After making changes, please reboot."
        )
        __show_popup(title, message)
        return False

    return True


def _unknown_compositor_checks():
    """
    Best-effort handling for unrecognised Wayland compositors.

    Logs a warning and checks uinput prerequisites.  Does NOT abort.
    """
    dte = (
        os.environ.get("XDG_SESSION_DESKTOP")
        or os.environ.get("DESKTOP_SESSION")
        or "unknown"
    )
    logger.warning(
        f"waylandChecks(): Unrecognised Wayland compositor (XDG_SESSION_DESKTOP='{dte}').  "
        "AutoKey will attempt to start in best-effort mode.  "
        "Text expansion may work if uinput is available.  "
        "Window title/class filtering will not be available.  "
        "Please report your compositor at https://github.com/autokey/autokey/issues/87"
    )

    ok, msg = _check_uinput_prerequisites()
    if not ok:
        logger.warning(
            f"waylandChecks(): uinput prerequisites not met ({msg}). "
            "Key injection may not work."
        )
        # Non-fatal for unknown compositors — let the user discover the issue
        # via clear log messages rather than a hard abort.

    return True


# ---------------------------------------------------------------------------
# Popup helpers
# ---------------------------------------------------------------------------

def __show_popup(title, message):
    """Show a popup using kdialog, zenity, or fall back to logging."""
    plain_message = message.replace("<br />", "\n").replace("<b>", "").replace("</b>", "")
    try:
        subprocess.run(
            f"kdialog --error '{plain_message}' --title '{title}'",
            shell=True, check=True,
        )
        return
    except Exception:
        pass
    try:
        subprocess.run(
            f"zenity --error --title='{title}' --text='{plain_message}'",
            shell=True, check=True,
        )
        return
    except Exception:
        pass
    logger.critical(f"[{title}] {plain_message}")


#  For testing purposes
if __name__ == '__main__':
    if not waylandChecks():
        print('waylandChecks() returned False')
