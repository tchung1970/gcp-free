# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a single-file Python utility (`gcp-free.py`) for managing Google Cloud Platform (GCP) compute instances, specifically designed for Free Tier usage. It provides a simplified command-line interface for creating and managing Ubuntu LTS AMD64 VMs with Free Tier eligible configurations.

**Key Design Principles:**
- Single VM enforcement to stay within Free Tier limits
- Pre-configured Free Tier defaults (e2-micro, us-west1-a, 30GB standard disk)
- User-friendly interface with progress indicators and validation
- Focus on Ubuntu LTS AMD64 Standard images (22.04, 24.04)

## Commands

### Running the Script
```bash
python3 gcp-free.py <command>
```

### Available Commands (in typical workflow order)
- `python3 gcp-free.py list` - List current VM instances
- `python3 gcp-free.py image` - List available Ubuntu LTS AMD64 Standard images with default marker
- `python3 gcp-free.py set` - Interactive configuration of project and image settings
- `python3 gcp-free.py create` - Create 'free-tier' VM with all defaults (2-3 minutes)
- `python3 gcp-free.py ssh` - SSH into the 'free-tier' VM
- `python3 gcp-free.py delete` - Delete the 'free-tier' VM with 3-minute timeout

## Configuration

### Environment File (~/.env)
The script reads configuration from `~/.env`:
- `GCP_PROJECT` - Your GCP project ID (required)
- `GCP_IMAGE` - Default Ubuntu image (optional, defaults to ubuntu-2204-jammy-v20250815)

### Interactive Setup
Use `python3 gcp-free.py set` for guided configuration:
- Project selection from your available GCP projects
- Image selection from 2 Ubuntu LTS Standard options (22.04/24.04)
- Automatic .env file management

## Architecture & Implementation Details

### Dependency Management
- `check_dependencies()` - Validates gcloud CLI installation and authentication
- Offers interactive installation guidance for missing dependencies
- Platform-specific installation instructions (macOS/Linux/Windows)

### VM Lifecycle Management
- **Pre-flight validation**: Checks VM existence before create/delete operations
- **Single instance enforcement**: Prevents creating multiple VMs
- **Timeout handling**: 3-minute timeout for delete operations with fallback options
- **Progress indication**: Custom Spinner class with animated progress feedback

### Core Functions
- `create_vm()` - VM creation with existence check and user-friendly image naming
- `ssh_vm()` - SSH connection to VM with existence validation
- `delete_vm()` - VM deletion with timeout and console fallback URLs
- `list_ubuntu_images()` - Filtered Ubuntu LTS AMD64 Standard image discovery with default markers
- `configure_settings()` - Interactive .env file management
- `check_dependencies()` - Dependency validation and installation guidance

### Image Management
- Filters to show only Ubuntu LTS AMD64 Standard images (no pro/accelerator/minimal variants)
- Sorted by Ubuntu version (22.04 before 24.04)
- Default image marking in listings
- Architecture filtering using `gcloud --filter="name~ubuntu AND architecture=X86_64"`

### Error Handling & User Experience
- Comprehensive error messages with suggested actions
- Command-line display for failed operations (for manual execution)
- Console URLs for manual VM management when operations timeout
- Graceful handling of missing dependencies and authentication

### Free Tier Optimization
- **Fixed defaults**: e2-micro machine, us-west1-a zone, 30GB pd-standard disk
- **Region selection**: us-west1-a (Free Tier eligible region)
- **Resource limits**: Single VM policy prevents accidental over-provisioning
- **Cost awareness**: All defaults chosen for Free Tier compatibility