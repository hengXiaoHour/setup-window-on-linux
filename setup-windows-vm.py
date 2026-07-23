#!/usr/bin/env python3
import os, sys, subprocess, shutil, json, time, urllib.request

HOME = os.path.expanduser("~")
LOCAL_BIN = f"{HOME}/.local/bin"
LOCAL_SHARE_APPS = f"{HOME}/.local/share/applications"
LOCAL_SHARE_ICONS = f"{HOME}/.local/share/icons"
STORAGE = f"{HOME}/windows"
CONTAINER = "windows"
SUDO = "sudo"

def run(cmd, capture=False, timeout=120):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=capture, text=True, timeout=timeout)
        if capture: return r.stdout.strip(), r.returncode
        return r.returncode
    except subprocess.TimeoutExpired:
        return 1

def check_sudo():
    r = subprocess.run(f"{SUDO} true 2>/dev/null", shell=True)
    if r.returncode != 0:
        print(f"[!] This script needs sudo. Run: sudo python3 {__file__}")
        sys.exit(1)

def step(n, title):
    print(f"\n[{n}] {title}...")

def check_prereqs():
    step("1/9", "Checking system prerequisites")
    kvm = os.path.exists("/dev/kvm")
    virt = int(subprocess.run("egrep -c '(vmx|svm)' /proc/cpuinfo", shell=True, capture_output=True, text=True).stdout.strip() or 0)
    cpu = subprocess.run("grep -m1 'model name' /proc/cpuinfo", shell=True, capture_output=True, text=True).stdout.strip()
    print(f"    KVM: {'OK' if kvm else 'MISSING'}, Virtualization: {virt} cores, CPU: {cpu}")
    if not kvm: print("    [!] /dev/kvm not found. Enable VT-x/AMD-V in BIOS.")
    assert kvm and virt > 0, "Missing virtualization support"

def install_docker():
    step("2/9", "Installing Docker")
    if shutil.which("docker"):
        print("    Docker already installed")
        return
    subprocess.run("curl -fsSL https://get.docker.com -o /tmp/get-docker.sh", shell=True, check=True, timeout=30)
    subprocess.run(f"{SUDO} sh /tmp/get-docker.sh", shell=True, check=True, timeout=120)
    subprocess.run(f"{SUDO} usermod -aG docker $USER", shell=True, timeout=10)
    subprocess.run(f"{SUDO} systemctl enable docker", shell=True, timeout=10)
    subprocess.run(f"{SUDO} systemctl start docker", shell=True, timeout=10)
    subprocess.run(f"{SUDO} chmod 666 /var/run/docker.sock", shell=True, timeout=10)
    print("    Docker installed")

def pull_image():
    step("3/9", "Pulling dockurr/windows image")
    run(f"docker pull dockurr/windows", timeout=300)

def run_container():
    step("4/9", "Starting Windows container")
    run(f"docker stop {CONTAINER} 2>/dev/null; docker rm {CONTAINER} 2>/dev/null")
    os.makedirs(STORAGE, exist_ok=True)
    cmd = (
        f"docker run -itd --name {CONTAINER} "
        f"-p 8006:8006 -p 3389:3389 "
        f"--device=/dev/kvm --cap-add NET_ADMIN "
        f"-e VERSION=11 -e RAM_SIZE=8G -e CPU_CORES=8 "
        f"-e DISK_SIZE=128G -e DISK_CACHE=writeback "
        f"-e WIDTH=2560 -e HEIGHT=1440 "
        f"-v {STORAGE}:/storage "
        f"--restart unless-stopped "
        f"dockurr/windows"
    )
    run(cmd)
    print("    Container started")

def download_icon():
    step("5/9", "Downloading Windows 11 icon")
    os.makedirs(LOCAL_SHARE_ICONS, exist_ok=True)
    url = "https://img.icons8.com/color/512/windows-11.png"
    try:
        urllib.request.urlretrieve(url, f"{LOCAL_SHARE_ICONS}/windows11.png")
    except:
        url2 = "https://raw.githubusercontent.com/HotCakeX/Harden-Windows-Security/main/images/PNGs/Windows11.png"
        urllib.request.urlretrieve(url2, f"{LOCAL_SHARE_ICONS}/windows11.png")

def install_rdp():
    step("6/9", "Installing RDP client")
    r1 = run("apt-cache show freerdp3-x11 2>/dev/null", capture=True)
    pkg = "freerdp3-x11" if r1[1] == 0 else "freerdp-x11"
    run(f"{SUDO} apt-get install -y -qq {pkg} 2>/dev/null", timeout=120)

def create_helper_script():
    step("7/9", "Creating helper scripts")
    os.makedirs(LOCAL_BIN, exist_ok=True)
    with open(f"{LOCAL_BIN}/windows-vm", "w") as f:
        f.write("""#!/bin/bash
docker start windows 2>/dev/null
sleep 3
xfreerdp3 /v:localhost /u:Docker /p:admin /cert:ignore /sound /f /dynamic-resolution /w:2560 /h:1440 /pwidth:339 /pheight:191 /scale:180
""")
    os.chmod(f"{LOCAL_BIN}/windows-vm", 0o755)
    print(f"    Created {LOCAL_BIN}/windows-vm")

def create_desktop_icon():
    step("8/9", "Creating desktop launcher")
    os.makedirs(LOCAL_SHARE_APPS, exist_ok=True)
    with open(f"{LOCAL_SHARE_APPS}/windows-vm.desktop", "w") as f:
        f.write(f"""[Desktop Entry]
Name=Windows 11
Comment=Run Windows 11 VM via RDP
Exec={LOCAL_BIN}/windows-vm
Icon=windows11
Terminal=false
Type=Application
Categories=System;
""")
    os.chmod(f"{LOCAL_SHARE_APPS}/windows-vm.desktop", 0o755)
    run("update-desktop-database ~/.local/share/applications 2>/dev/null")
    run("gtk-update-icon-cache ~/.local/share/icons 2>/dev/null")

def verify_and_fix():
    step("9/9", "Verifying installation")
    checks = [
        ("Container running", f"docker inspect -f '{{{{.State.Status}}}}' {CONTAINER} 2>/dev/null", "running"),
        ("Port 3389 exposed", f"docker port {CONTAINER} 3389 2>/dev/null", "3389"),
        ("Port 8006 exposed", f"docker port {CONTAINER} 8006 2>/dev/null", "8006"),
        ("Helper script", f"test -x {LOCAL_BIN}/windows-vm && echo yes", "yes"),
        ("Desktop file", f"test -f {LOCAL_SHARE_APPS}/windows-vm.desktop && echo yes", "yes"),
        ("Icon file", f"test -f {LOCAL_SHARE_ICONS}/windows11.png && echo yes", "yes"),
        ("RDP client", f"sh -c 'which xfreerdp3 || which xfreerdp' && echo yes", "yes"),
        ("Docker autostart", f"{SUDO} systemctl is-enabled docker 2>/dev/null", "enabled"),
    ]
    failed = []
    for label, cmd, expected in checks:
        out, _ = run(cmd, capture=True)
        ok = expected in out
        print(f"    {'✓' if ok else '✗'} {label}")
        if not ok: failed.append(label)

    if failed:
        print(f"\n    [!] Failed: {', '.join(failed)}")
        sys.exit(1)
    print("\n    All checks passed!")

def main():
    print("╔══════════════════════════════════════╗")
    print("║  Windows 11 VM Setup Script         ║")
    print("╚══════════════════════════════════════╝")
    check_sudo()
    check_prereqs()
    install_docker()
    pull_image()
    run_container()
    download_icon()
    install_rdp()
    create_helper_script()
    create_desktop_icon()
    time.sleep(2)
    verify_and_fix()
    print(f"\n{'='*45}")
    print("Setup complete! Click 'Windows 11' in your app menu.")
    print(f"Or run: {LOCAL_BIN}/windows-vm")
    print(f"Browser fallback: http://localhost:8006")
    print("Username: Docker | Password: admin")
    print(f"{'='*45}")

if __name__ == "__main__":
    main()
