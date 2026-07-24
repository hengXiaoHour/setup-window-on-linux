# Windows 11 VM on Linux — One Command Setup

Run Windows 11 inside a lightweight KVM virtual machine on Linux with near-native performance. Auto-installs everything — no manual config.

## What you get

- Full Windows 11 desktop in **fullscreen RDP** (zero latency)
- RDP at native resolution with **200% display scaling** (no tiny/blurry UI)
- **Desktop icon** — single click to launch
- **Auto-starts** on boot
- **Persistent storage** — stop/restart without losing data
- **Browser fallback** at `http://localhost:8006`

## Quick Start

```bash
git clone https://github.com/hengXiaoHour/setup-window-on-linux
cd setup-window-on-linux
sudo python3 setup-windows-vm.py
```

That's it. After the script finishes, search **"Windows 11"** in your app menu and click it.

## Prerequisites

- A Linux machine with **KVM support** (Intel VT-x / AMD-V)
  - Check: `ls /dev/kvm` should exist
  - If missing, enable virtualization in BIOS
- **At least 16GB RAM** recommended (8GB for Windows, rest for Linux)
- **~5GB free space** for the Docker image + **128GB** for the Windows disk
- Internet connection for downloading Windows

## What the script does

| Step | What |
|------|------|
| 1 | Checks KVM and CPU virtualization |
| 2 | Installs Docker (if missing) |
| 3 | Pulls `dockurr/windows` image |
| 4 | Creates container with optimized settings |
| 5 | Downloads Windows 11 icon |
| 6 | Installs `xfreerdp3` (RDP client) |
| 7 | Creates launcher script (`~/.local/bin/windows-vm`) |
| 8 | Creates desktop entry in app menu |
| 9 | Verifies everything is running |

## Configuration

Edit `setup-windows-vm.py` variables at the top before running:

```python
RAM_SIZE = "8G"       # RAM for Windows (half of your total)
CPU_CORES = "8"        # CPU cores for Windows
DISK_SIZE = "128G"     # Windows disk size
WIDTH = "2560"         # Your monitor width
HEIGHT = "1440"        # Your monitor height
```

## Usage

After setup, click **Windows 11** in your app menu. Or run:

```bash
~/.local/bin/windows-vm
```

### Controls

| Key | Action |
|-----|--------|
| `Ctrl + Alt + Enter` | Toggle fullscreen |
| `Ctrl + Alt + C` | Gracefully disconnect |

### Login

Username: `Docker` | Password: `admin`

### Browser fallback

If RDP doesn't work for some reason, open `http://localhost:8006` in a browser.

## How it works

- **Hypervisor**: QEMU/KVM (near-native CPU/memory performance)
- **Container**: [dockurr/windows](https://github.com/dockur/windows) handles Windows download, install, and boot
- **Display**: xfreerdp3 connects via RDP (much less latency than VNC)
- **Scaling**: Physical dimensions passed to Windows so it auto-selects 200% DPI
- **Disk**: Writeback cache for faster I/O

## Troubleshooting

**"Windows 11" icon doesn't show in app menu**
Log out and back in, or run: `update-desktop-database ~/.local/share/applications`

**RDP connection fails**
Run the browser fallback at `http://localhost:8006` and make sure Remote Desktop is enabled in Windows (Settings → System → Remote Desktop).

**UI is too small or too large in RDP**
Adjust `WIDTH`/`HEIGHT` in the script to match your monitor, then rerun.

**No internet in Windows (school/corporate WiFi)**
Some networks block Docker NAT DNS. Inside Windows, run:
```cmd
netsh interface ip set dns name="Ethernet" source=static addr=8.8.8.8
```

**Container won't start**
Check logs: `docker logs windows`

## Notes

- The first run downloads Windows 11 from Microsoft (~5GB), which takes a few minutes
- Windows data persists in `~/windows/` on your host
- The container restarts automatically on boot and crash

## Credits

- [dockurr/windows](https://github.com/dockur/windows) for the Windows-in-Docker container
- [FreeRDP](https://www.freerdp.com/) for the RDP client
- [icons8](https://icons8.com) for the Windows 11 icon
