#!/usr/bin/env python3
# gcp-free.py
# by Thomas Chung
# on 2025-08-20
#
# Google Cloud Platform (GCP) Free Tier VM Management Script
#
# This script provides a simple command-line interface for managing GCP compute instances
# optimized for Free Tier usage. It focuses on creating single Ubuntu LTS AMD64 VMs
# with Free Tier eligible configurations.
#
# Key Features:
# 1. Single VM enforcement - prevents creating multiple instances to stay within Free Tier
# 2. Pre-configured defaults - e2-micro, us-west1-a zone, 30GB standard disk
# 3. Interactive setup - configure GCP project and Ubuntu image via 'set' command
# 4. Smart validation - checks VM existence before create/delete operations
# 5. Progress indicators - animated spinners for long-running operations
# 6. Ubuntu LTS focus - filtered list of AMD64 LTS images (22.04, 24.04)
#
# Prerequisites:
# - Google Cloud SDK (gcloud) installed and authenticated
# - GCP project with Compute Engine API enabled
# - ~/.env file with GCP_PROJECT set (use 'set' command to configure)
#
# Usage:
#   python3 gcp-free.py list     - List VM instances
#   python3 gcp-free.py image    - List Ubuntu LTS AMD64 images
#   python3 gcp-free.py create   - Create Free Tier VM with defaults
#   python3 gcp-free.py ssh      - SSH into the 'free-tier' VM
#   python3 gcp-free.py delete   - Delete the 'free-tier' VM
#   python3 gcp-free.py set      - Configure project and image settings

import subprocess
import sys
import os
import time
import threading
import atexit
from pathlib import Path

# Load environment variables from ~/.env
def load_env():
    env_path = Path.home() / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

DEFAULT_PROJECT = os.getenv('GCP_PROJECT', 'your-default-project')
DEFAULT_ZONE = "us-west1-a"
DEFAULT_IMAGE = os.getenv('GCP_IMAGE', 'ubuntu-2204-jammy-v20250815')

def check_dependencies():
    """Check for required dependencies and offer to install if missing."""
    missing_deps = []
    
    # Check for gcloud CLI
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            missing_deps.append('gcloud')
    except FileNotFoundError:
        missing_deps.append('gcloud')
    
    # Check if gcloud is authenticated
    try:
        result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE'], 
                              capture_output=True, text=True)
        if 'ACTIVE' not in result.stdout:
            missing_deps.append('gcloud-auth')
    except:
        missing_deps.append('gcloud-auth')
    
    if missing_deps:
        print("⚠️  Missing dependencies detected:")
        print()
        
        for dep in missing_deps:
            if dep == 'gcloud':
                print("❌ Google Cloud SDK (gcloud) is not installed")
                print("   Required for managing GCP compute instances")
                install = input("   Install Google Cloud SDK? (Y/n): ").strip().lower()
                if install != 'n':
                    print("\n📦 Installing Google Cloud SDK...")
                    if sys.platform == "darwin":  # macOS
                        print("   Run: brew install --cask google-cloud-sdk")
                        print("   Or visit: https://cloud.google.com/sdk/docs/install")
                    elif sys.platform.startswith("linux"):  # Linux
                        print("   Run: curl https://sdk.cloud.google.com | bash")
                        print("   Or visit: https://cloud.google.com/sdk/docs/install")
                    else:  # Windows
                        print("   Visit: https://cloud.google.com/sdk/docs/install")
                    print()
            
            elif dep == 'gcloud-auth':
                print("❌ Google Cloud SDK is not authenticated")
                print("   Required for accessing your GCP project")
                auth = input("   Authenticate with Google Cloud? (Y/n): ").strip().lower()
                if auth != 'n':
                    print("\n🔐 Authenticating with Google Cloud...")
                    try:
                        subprocess.run(['gcloud', 'auth', 'login'], check=True)
                        print("✅ Authentication successful!")
                    except subprocess.CalledProcessError:
                        print("❌ Authentication failed. Please try manually:")
                        print("   gcloud auth login")
                    except FileNotFoundError:
                        print("❌ gcloud not found. Please install Google Cloud SDK first.")
                    print()
        
        print("Please restart the script after installing dependencies.")
        return False
    
    return True

# Spinner implementation
_SPINNERS = {
    "dots": ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏'],
    "line": ['-', '\\', '|', '/'],
    "triangle": ['◢','◣','◤','◥'],
    "arrow": ['←','↖','↑','↗','→','↘','↓','↙']
}

_GREEN = "\033[92m"
_RED   = "\033[91m"
_RESET = "\033[0m"

class Spinner:
    def __init__(self, text="Loading...", spinner="dots", interval=0.08, stream=sys.stdout):
        self.text = text
        self.spinner = spinner
        self.interval = interval
        self.stream = stream

        self._frames = self._get_frames(spinner)
        self._stop = threading.Event()
        self._thread = None
        self._cursor_hidden = False
        self._render_lock = threading.Lock()
        self._last_len = 0

    def _get_frames(self, name):
        if isinstance(name, (list, tuple)) and name:
            return list(name)
        return _SPINNERS.get(str(name), _SPINNERS["dots"])

    def _hide_cursor(self):
        if not self._cursor_hidden:
            self.stream.write("\x1b[?25l")
            self.stream.flush()
            self._cursor_hidden = True

    def _show_cursor(self):
        if self._cursor_hidden:
            self.stream.write("\x1b[?25h")
            self.stream.flush()
            self._cursor_hidden = False

    def _render(self, s: str):
        pad = max(0, self._last_len - len(s))
        self.stream.write("\r" + s + (" " * pad))
        self.stream.flush()
        self._last_len = len(s)

    def _loop(self):
        i = 0
        self._hide_cursor()
        while not self._stop.is_set():
            frame = self._frames[i % len(self._frames)]
            line = f"{frame} {self.text}"
            with self._render_lock:
                self._render(line)
            i += 1
            end = time.time() + self.interval
            while time.time() < end:
                if self._stop.is_set():
                    break
                time.sleep(0.01)

    def _clear_line(self):
        self._render("")
        self.stream.write("\r")
        self.stream.flush()
        self._last_len = 0

    def start(self):
        if self._thread and self._thread.is_alive():
            return self
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join()
        with self._render_lock:
            self._clear_line()
        self._show_cursor()

    def succeed(self, text="Done."):
        self.stop()
        self.stream.write(f"{_GREEN}✔{_RESET} {text}\n")
        self.stream.flush()

    def fail(self, text="Failed."):
        self.stop()
        self.stream.write(f"{_RED}✖{_RESET} {text}\n")
        self.stream.flush()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.fail(str(exc) if str(exc) else "Failed.")
        else:
            self.succeed("Done.")

_instances = []
def _restore_all():
    for sp in _instances:
        try:
            sp._show_cursor()
        except Exception:
            pass
atexit.register(_restore_all)

def run_cmd(cmd):
    return subprocess.check_output(cmd, text=True).strip()

def list_ubuntu_images():
    cmd = "gcloud compute images list --filter=\"name~ubuntu AND architecture=X86_64\" --format=\"value(name)\" | egrep '2204|2404' | egrep -v 'accelerator|pro|minimal'"
    # print(f"Running: {cmd}")
    # print()
    
    # Run the actual command
    standard_output = subprocess.check_output(cmd, shell=True, text=True).strip()
    standard_images = standard_output.splitlines() if standard_output else []
    
    for idx, img in enumerate(standard_images, 1):
        marker = " (default)" if img == DEFAULT_IMAGE else ""
        print(f"{idx}. {img}{marker}")
    print()  # Add extra blank line

def list_vms():
    cmd = [
        "gcloud", "compute", "instances", "list",
        f"--project={DEFAULT_PROJECT}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.rstrip())  # Remove trailing whitespace/newlines
        print()  # Add blank line after output
    else:
        print("Listed 0 items.")
        print()  # Add blank line after output


def create_vm(vm_name="free-tier", machine_type="e2-micro"):
    # Check if VM already exists
    check_cmd = [
        "gcloud", "compute", "instances", "describe", vm_name,
        f"--project={DEFAULT_PROJECT}",
        f"--zone={DEFAULT_ZONE}",
        "--format=value(name)"
    ]
    
    try:
        subprocess.run(check_cmd, capture_output=True, text=True, check=True)
        print(f"✖ VM '{vm_name}' already exists.")
        print()
        return
    except subprocess.CalledProcessError:
        # VM doesn't exist, proceed with creation
        pass
    
    image = DEFAULT_IMAGE
    
    # Get user-friendly image name for display
    if "2204" in image and "minimal" in image:
        image_desc = "Ubuntu 22.04 LTS Minimal"
    elif "2404" in image and "minimal" in image:
        image_desc = "Ubuntu 24.04 LTS Minimal"
    elif "2204" in image:
        image_desc = "Ubuntu 22.04 LTS Standard"
    elif "2404" in image:
        image_desc = "Ubuntu 24.04 LTS Standard"
    else:
        image_desc = image
    
    cmd = [
        "gcloud", "compute", "instances", "create", vm_name,
        f"--project={DEFAULT_PROJECT}",
        f"--zone={DEFAULT_ZONE}",
        f"--machine-type={machine_type}",
        f"--image={image}",
        "--image-project=ubuntu-os-cloud",
        "--boot-disk-size=30GB",
        "--boot-disk-type=pd-standard"
    ]
    
    # print(f"Running: {' '.join(cmd)}")
    print("(this can take up to 3 mins)")
    
    spinner = Spinner(f"Creating VM '{vm_name}' with {image_desc}...", "dots").start()
    _instances.append(spinner)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        spinner.succeed(f"VM '{vm_name}' created successfully!")
        if result.stdout:
            print(result.stdout)
        print()  # Add extra blank line
    except subprocess.CalledProcessError as e:
        spinner.fail(f"Failed to create VM '{vm_name}'")
        print(f"Command: {' '.join(cmd)}")
        if e.stderr:
            print(e.stderr)
        print()  # Add extra blank line


def ssh_vm(vm_name):
    # Check if VM exists first
    check_cmd = [
        "gcloud", "compute", "instances", "describe", vm_name,
        f"--project={DEFAULT_PROJECT}",
        f"--zone={DEFAULT_ZONE}",
        "--format=value(name)"
    ]
    
    try:
        subprocess.run(check_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        print(f"✖ VM '{vm_name}' not found.")
        print()
        return
    
    cmd = [
        "gcloud", "compute", "ssh", vm_name,
        f"--project={DEFAULT_PROJECT}",
        f"--zone={DEFAULT_ZONE}"
    ]
    
    # print(f"Running: {' '.join(cmd)}")
    # print()
    
    # Use subprocess.run without capture_output to allow interactive SSH
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"✖ Failed to SSH to VM '{vm_name}'")
        print(f"Command: {' '.join(cmd)}")
        if e.stderr:
            print(e.stderr)
        print()


def delete_vm(vm_name):
    # Check if VM exists first
    check_cmd = [
        "gcloud", "compute", "instances", "describe", vm_name,
        f"--project={DEFAULT_PROJECT}",
        f"--zone={DEFAULT_ZONE}",
        "--format=value(name)"
    ]
    
    try:
        subprocess.run(check_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        print(f"✖ VM '{vm_name}' not found.")
        print()
        return
    
    cmd = [
        "gcloud", "compute", "instances", "delete", vm_name,
        f"--project={DEFAULT_PROJECT}",
        f"--zone={DEFAULT_ZONE}",
        "--quiet"
    ]
    
    # print(f"Running: {' '.join(cmd)}")
    print("(this can take up to 3 mins)")
    
    spinner = Spinner(f"Deleting VM '{vm_name}'...", "dots").start()
    _instances.append(spinner)
    
    try:
        # Set timeout to 3 minutes (180 seconds)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=180)
        spinner.succeed(f"VM '{vm_name}' deleted successfully!")
        if result.stdout:
            print(result.stdout)
        print()  # Add extra blank line
    except subprocess.TimeoutExpired:
        spinner.fail(f"Delete operation timed out after 3 minutes")
        print(f"The deletion may still be in progress. You can:")
        print(f"1. Check status: python {sys.argv[0]} list")
        print(f"2. Delete manually via console:")
        print(f"   https://console.cloud.google.com/compute/instances?project={DEFAULT_PROJECT}")
        print(f"3. Or run: gcloud compute instances delete {vm_name} --project={DEFAULT_PROJECT} --zone={DEFAULT_ZONE}")
        print()  # Add extra blank line
    except subprocess.CalledProcessError as e:
        spinner.fail(f"Failed to delete VM '{vm_name}'")
        print(f"Command: {' '.join(cmd)}")
        if e.stderr:
            print(e.stderr)
        print()  # Add extra blank line

def configure_settings():
    env_path = Path.home() / '.env'
    
    print("Configure Default Settings")
    print("=" * 30)
    
    # Current values
    current_project = os.getenv('GCP_PROJECT', 'your-default-project')
    current_image = os.getenv('GCP_IMAGE', 'ubuntu-2204-jammy-v20250815')
    
    print(f"\nCurrent GCP_PROJECT: {current_project}")
    
    # Get new project
    new_project = input("Enter GCP Project ID (or press Enter to keep current): ").strip()
    
    # Get available images using same command as image listing
    cmd = "gcloud compute images list --filter=\"name~ubuntu AND architecture=X86_64\" --format=\"value(name)\" | egrep '2204|2404' | egrep -v 'accelerator|pro|minimal'"
    standard_output = subprocess.check_output(cmd, shell=True, text=True).strip()
    available_images = standard_output.splitlines() if standard_output else []
    
    # Create image options with descriptions
    images = []
    for img in available_images:
        if "2204" in img:
            desc = "Ubuntu 22.04 LTS Standard"
        elif "2404" in img:
            desc = "Ubuntu 24.04 LTS Standard"
        else:
            desc = "Ubuntu LTS Standard"
        images.append((img, desc))
    
    print(f"\nCurrent Image: {current_image}")
    print("Available Ubuntu Images:")
    for i, (img, desc) in enumerate(images, 1):
        marker = " (current)" if img == current_image else ""
        print(f"  {i}. {img}{marker}")
    
    new_image_choice = input(f"Choose image (1-{len(images)}, or press Enter to keep current): ").strip()
    
    # Update settings
    changes_made = False
    lines = []
    project_found = False
    image_found = False
    
    # Read existing file
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('GCP_PROJECT='):
                    if new_project:
                        lines.append(f'GCP_PROJECT={new_project}')
                        changes_made = True
                    else:
                        lines.append(line)
                    project_found = True
                elif line.startswith('GCP_IMAGE='):
                    if new_image_choice and new_image_choice.isdigit():
                        idx = int(new_image_choice) - 1
                        if 0 <= idx < len(images):
                            lines.append(f'GCP_IMAGE={images[idx][0]}')
                            changes_made = True
                        else:
                            lines.append(line)
                    else:
                        lines.append(line)
                    image_found = True
                else:
                    lines.append(line)
    
    # Add missing entries
    if new_project and not project_found:
        lines.append(f'GCP_PROJECT={new_project}')
        changes_made = True
    
    if new_image_choice and new_image_choice.isdigit() and not image_found:
        idx = int(new_image_choice) - 1
        if 0 <= idx < len(images):
            lines.append(f'GCP_IMAGE={images[idx][0]}')
            changes_made = True
    
    # Write back to file if changes were made
    if changes_made:
        with open(env_path, 'w') as f:
            for line in lines:
                if line:  # Skip empty lines
                    f.write(line + '\n')
        
        print(f"\n✓ Settings updated!")
        if new_project:
            print(f"   Project: {new_project}")
        if new_image_choice and new_image_choice.isdigit():
            idx = int(new_image_choice) - 1
            if 0 <= idx < len(images):
                print(f"   Image: {images[idx][0]}")
        print("Please restart the script for changes to take effect.")
    else:
        print("\n✓ No changes made.")
        
    print(f"\nOther defaults (Free Tier eligible):")
    print(f"  VM Name: free-tier")
    print(f"  Zone: us-west1-a")
    print(f"  Machine: e2-micro")
    print(f"  Boot Disk: 30GB pd-standard")
    print()  # Add extra blank line


def usage():
    if DEFAULT_PROJECT == 'your-default-project':
        print("ERROR: GCP_PROJECT not found in ~/.env file")
        print("Please create ~/.env with: GCP_PROJECT=your-project-id\n")
        return
    
    print("Defaults (Free Tier eligible):")
    print(f"  VM Name: free-tier")
    print(f"  Zone: {DEFAULT_ZONE}")
    print(f"  Machine: e2-micro (0.25 vCPU, 1GB RAM)")
    print(f"  Image: {DEFAULT_IMAGE}")
    print(f"  Boot Disk: 30GB pd-standard\n")
    print("Usage:")
    print("  python gcp-free.py list")
    print("      List VM instances.\n")
    print("  python gcp-free.py image")
    print("      List Ubuntu LTS AMD64 images.\n")
    print("  python gcp-free.py set")
    print("      Configure default settings.\n")
    print("  python gcp-free.py create")
    print("      Create a VM using all defaults (takes 2-3 minutes).\n")
    print("  python gcp-free.py ssh")
    print("      SSH into the 'free-tier' VM.\n")
    print("  python gcp-free.py delete")
    print("      Delete the 'free-tier' VM (takes 2-3 minutes).\n")

def main():
    # Check dependencies first
    if not check_dependencies():
        return
        
    if len(sys.argv) < 2:
        usage()
        return

    cmd = sys.argv[1]

    if cmd == "list":
        list_vms()
    elif cmd == "image":
        list_ubuntu_images()
    elif cmd == "create" and len(sys.argv) == 2:
        create_vm()
    elif cmd == "ssh" and len(sys.argv) == 2:
        ssh_vm("free-tier")
    elif cmd == "delete" and len(sys.argv) == 2:
        delete_vm("free-tier")
    elif cmd == "set" and len(sys.argv) == 2:
        configure_settings()
    else:
        usage()

if __name__ == "__main__":
    main()
