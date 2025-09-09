# GCP Free Tier Manager

A simple Python utility for managing Google Cloud Platform Free Tier virtual machines. Designed specifically for creating and managing single Ubuntu LTS instances within Free Tier limits.

## Features

- 🚀 **One-command VM operations** - Create, SSH, and delete VMs with simple commands
- 💰 **Free Tier optimized** - Pre-configured with e2-micro, us-west1-a, and 30GB disk
- 🛡️ **Single VM enforcement** - Prevents accidental multi-VM creation to stay within limits
- 🔧 **Interactive setup** - Guided configuration for GCP project and Ubuntu image selection
- 📊 **Progress indicators** - Animated spinners for long-running operations
- ✅ **Smart validation** - Checks VM existence and dependencies before operations

## Quick Start

### Prerequisites

- Google Cloud SDK (`gcloud`) installed and authenticated
- GCP project with Compute Engine API enabled
- Python 3.6+

### Installation

1. Clone or download `gcp-free.py`
2. Set up your project configuration:
   ```bash
   python3 gcp-free.py set
   ```

### Basic Usage

```bash
# List available Ubuntu images
python3 gcp-free.py image

# Create a Free Tier VM (takes 3-4 minutes with preparation)
python3 gcp-free.py create

# SSH into your VM
python3 gcp-free.py ssh

# List your VMs
python3 gcp-free.py list

# Delete the VM (takes 2-3 minutes)
python3 gcp-free.py delete
```

## Commands

| Command | Description |
|---------|-------------|
| `list` | List current VM instances |
| `image` | List available Ubuntu LTS AMD64 images |
| `set` | Configure GCP project and default image |
| `create` | Create 'free-tier' VM with interactive image selection |
| `ssh` | SSH into the 'free-tier' VM |
| `delete` | Delete the 'free-tier' VM |

## Configuration

The script reads configuration from `~/.env`:

```bash
GCP_PROJECT=your-project-id
GCP_IMAGE=ubuntu-2204-jammy-v20250815  # optional
```

Use `python3 gcp-free.py set` for interactive configuration.

## Free Tier Defaults

The script uses these Free Tier eligible defaults:

- **Machine Type**: e2-micro (0.25 vCPU, 1GB RAM)
- **Zone**: us-west1-a (Free Tier eligible region)
- **Boot Disk**: 30GB pd-standard
- **Image**: Ubuntu 22.04 LTS Standard (AMD64)
- **VM Name**: free-tier

## Supported Images

The script filters for Ubuntu LTS Standard images only:
- Ubuntu 22.04 LTS Standard (`ubuntu-2204-jammy-v20250815`)
- Ubuntu 24.04 LTS Standard (`ubuntu-2404-noble-amd64-v20250819`)

*Note: Pro, accelerator, and minimal variants are excluded to keep the selection simple.*

## Dependency Management

The script automatically checks for:
- Google Cloud SDK installation
- Active gcloud authentication

If dependencies are missing, it provides platform-specific installation guidance.

## Safety Features

- **Existence checks**: Verifies VM state before create/delete operations
- **Single VM limit**: Prevents creating multiple VMs accidentally
- **Timeout handling**: 3-minute timeout for operations with fallback options
- **Interactive confirmation**: Built-in gcloud safety prompts

## Examples

### First-time setup
```bash
# Configure your GCP project
python3 gcp-free.py set

# Create your first VM (prompts for image, includes 1-min preparation)
python3 gcp-free.py create

# Connect to it
python3 gcp-free.py ssh
```

### Daily workflow
```bash
# Check if VM is running
python3 gcp-free.py list

# Connect to existing VM
python3 gcp-free.py ssh

# Clean up when done
python3 gcp-free.py delete
```

## Troubleshooting

### VM won't boot
- Ensure you're using AMD64 images (not ARM64)
- Check that e2-micro supports your selected image

### SSH connection fails
- Verify VM is in RUNNING state: `python3 gcp-free.py list`
- Check firewall rules allow SSH (default: enabled)
- Wait a moment after creation for SSH daemon to start

### Dependency issues
- Run `gcloud auth list` to verify authentication
- Use `python3 gcp-free.py set` to reconfigure if needed

## Architecture

Single-file Python script with these key components:

- **Spinner class**: Custom progress indicators
- **Environment management**: Automatic ~/.env file handling  
- **Command filtering**: Advanced gcloud filter expressions
- **Error handling**: Comprehensive validation and user feedback

## Free Tier Compliance

This tool is designed to help you stay within GCP Free Tier limits:

- **Always Free**: e2-micro instances in specific regions
- **30GB**: Standard persistent disk storage
- **Single VM**: Prevents accidental over-provisioning
- **Region lock**: us-west1-a for Free Tier eligibility

*Always verify current Free Tier terms at [cloud.google.com/free](https://cloud.google.com/free)*

## License

MIT License - feel free to modify and distribute.

## Contributing

This is a simple utility script. Feel free to fork and customize for your needs!