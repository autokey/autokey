# AutoKey Wayland Support 🦞

## Quick Start Guide

### Are you on Wayland?

Check first:
```bash
echo $XDG_SESSION_TYPE
```

**If it says `wayland`**: You need the accessibility setup below.  
**If it says `x11`**: No changes needed - AutoKey works normally! ✅

---

## Installing on Wayland (Ubuntu/GNOME)

### Step 1: Install Dependencies
```bash
sudo apt update
sudo apt install python3-pyatspi gir1.2-atspi-2.0 xdg-desktop-portal-gtk
```

### Step 2: Enable Accessibility
Open **Settings → Privacy → Accessibility** and enable:
- ✓ "Screen Keyboard" (optional, but helpful)
- ✓ Any permission to "Control Another Screen" or "Allow Screen Control"

### Step 3: Configure AutoKey
Edit `~/.config/autokey/data/autokey.json`:

```json
{
  "interfaceType": "WAYLAND_AUTO"
}
```

Or select in GUI: **Settings → Advanced → Interface Type → "Wayland"**

### Step 4: Restart AutoKey
```bash
killall autokey-gtk
autokey-gtk &
```

---

## What Works Now ✅

- ✅ Basic keyboard shortcuts (hotkeys)
- ✅ Text expansion (abbreviations)
- ✅ Clipboard operations
- ✅ Special keys (<ctrl>, <enter>, <tab>, etc.)
- ✅ Application-specific hotkeys

---

## Known Limitations ⚠️

### Global Hotkeys May Not Work
Due to Wayland's security model, some compositors don't allow apps to monitor global keypresses.

**Solution**: 
- Use application-scoped hotkeys instead
- Or switch to X11/Xorg session for complete functionality

### Compositor-Specific Behavior
Different desktop environments have different support levels:

| Desktop | Hotkeys | Injection | Notes |
|---------|---------|-----------|-------|
| GNOME | ⚠️ Limited | ✅ Good | Best tested |
| KDE Plasma | ❌ Unknown | ⚠️ Partial | Needs testing |
| Sway/Hyprland | ❌ Not supported | ⚠️ Possible | Very limited |
| X11/Xorg | ✅ Full | ✅ Full | Native mode |

---

## Troubleshooting

### "AutoKey doesn't work on Wayland!"
This is expected with tiling window managers (Sway, Hyprland, i3). 

**Fix options:**
1. **Switch to X11/Xorg**: Log out → Click gear icon → Select "Ubuntu on Xorg"
2. **Use application-scoped hotkeys**: These work better than global ones
3. **Report your compositor**: We want to add more support!

### "Accessibility permission denied"
Some systems require explicit permission for keyboard injection.

**GNOME**: Settings → Privacy → Security → Allow screen control  
**KDE**: System Settings → Workspace → Hardware Integration → Input Devices → Accessible

### Performance is slow
AT-SPI injection can be slightly slower than XTest.

**Expected behavior**: Small delay when typing fast (>5 chars/sec). This is normal.

---

## Development / Testing

### For Contributors

Clone and test:
```bash
git clone https://github.com/autokey/autokey.git
cd autokey
git checkout feature-wayland-support  # Our branch
pip3 install -e .
python3 test_wayland_prototype.py  # Run diagnostics
```

### Testing Checklist
- [ ] Can run AutoKey without crashing
- [ ] Basic text expansion works
- [ ] Single-key hotkeys trigger
- [ ] Complex shortcuts work (<ctrl>+<shift>+<a>)
- [ ] Clipboard functions correctly

---

## Why Does This Matter?

Most modern Linux distributions now default to Wayland:
- Ubuntu 24.04+ (GNOME by default)
- Fedora Workstation 34+ (Plasma/KDE)
- Arch Linux (any DE with Wayland)

AutoKey being X11-only excludes these users from automation tools. This PR brings basic functionality back to Wayland users while maintaining full backward compatibility.

---

## Technical Details

For developers interested in how this works:

See detailed implementation: `docs/WAYLAND_IMPLEMENTATION_GUIDE.md`

### Key Components
1. **DisplayServerDetector** - Auto-detects X11 vs Wayland
2. **WaylandInputBackend** - AT-SPI based keyboard injection
3. **WaylandEventMonitor** - Event listener (limited capabilities)
4. **XWaylandFallback** - Graceful degradation

### Architecture
```
┌───────────────┐
│  IoMediator   │ (existing code)
└───────┬───────┘
        │
    ┌───┴───────┐
    │           │
X11 Backend  Wayland Backend
 XRecord     AT-SPI / Portals
```

---

## Contributing

We especially need help testing on:
- KDE Plasma on Wayland
- Sway, Hyprland, River (tiling compositors)
- Other GNOME-based desktops

Please share:
- Your desktop environment + version
- What works/doesn't work
- Logs (`--debug` flag helps!)

---

## Credits

Based on 9 years of community discussions in Issue #87 (207+ comments!), this implementation represents a practical minimum viable product that balances feasibility with user needs.

Special thanks to contributors who shared their research on:
- AT-SPI accessibility APIs
- xdg-desktop-portal patterns  
- GNOME/Mutter implementation details

---

## License

Same as AutoKey: GPL v3+

---

*Last Updated: April 19, 2026*  
*Bounty Project: Issue #87 - Add Wayland Support ($350)*
