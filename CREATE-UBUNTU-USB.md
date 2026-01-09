# Create Ubuntu Bootable USB (24.04 LTS or 25.10)

Complete guide to creating a bootable USB installer for Ubuntu on your RTX 5090 server.

---

## Which Ubuntu Version?

### Ubuntu 24.04 LTS (Recommended for Servers) ✅

**Advantages:**
- ✅ **5 years of support** (until April 2029)
- ✅ **More stable** - tested for production
- ✅ **Security updates** guaranteed
- ✅ **Best for AI servers** - set and forget

**Recommended for:** AI servers, production systems, long-term deployments

### Ubuntu 25.10 (Latest Features) ⚡

**Advantages:**
- ⚡ **Newest kernel** (6.11+)
- ⚡ **Latest packages** and features
- ⚡ **Cutting-edge hardware support**

**Disadvantages:**
- ⚠️ **Only 9 months support** (until July 2026)
- ⚠️ **Less tested** in production
- ⚠️ **Must upgrade** every 9 months

**Recommended for:** Testing, development, enthusiasts who upgrade frequently

---

## Our Recommendation

**For your AI server: Use Ubuntu 24.04 LTS**

**Why?**
- Your AI server should be stable and reliable
- You don't want to upgrade the OS every 9 months
- LTS versions are battle-tested for server workloads
- NVIDIA drivers work perfectly on 24.04 LTS

**However:** Both versions work with our one-click installer! The choice is yours.

---

## Prerequisites

**What You Need:**
- USB flash drive (8GB minimum, 16GB recommended)
- Computer with internet connection (Windows, Mac, or Linux)
- ~30 minutes

**⚠️ WARNING:** All data on the USB drive will be erased!

---

## Method 1: Windows (Recommended - Easiest)

### Using Rufus (Best Tool)

**Step 1: Download Ubuntu ISO**

**For Ubuntu 24.04 LTS (Recommended):**
1. Go to: https://ubuntu.com/download/desktop
2. Click **"Download Ubuntu 24.04 LTS"**
3. Save `ubuntu-24.04-desktop-amd64.iso` (~5.7GB)
4. Wait for download to complete

**For Ubuntu 25.10 (Latest):**
1. Go to: https://ubuntu.com/download/desktop
2. Click **"Download Ubuntu 25.10"** (or look under "Alternative downloads")
3. Save `ubuntu-25.10-desktop-amd64.iso` (~5.9GB)
4. Wait for download to complete

**Step 2: Download Rufus**

1. Go to: https://rufus.ie/
2. Click **"Rufus 4.x"** (latest version)
3. Download `rufus-4.x.exe` (~1.5MB)
4. No installation needed - it's portable

**Step 3: Insert USB Drive**

1. Plug USB drive into your Windows PC
2. Backup any data on the USB (will be erased!)
3. Note the drive letter (e.g., D:, E:, F:)

**Step 4: Create Bootable USB with Rufus**

1. **Run Rufus** (double-click rufus-4.x.exe)
2. **Device**: Select your USB drive from dropdown
3. **Boot selection**: Click **"SELECT"** button
   - Browse to downloaded ISO file:
     - `ubuntu-24.04-desktop-amd64.iso` (LTS), OR
     - `ubuntu-25.10-desktop-amd64.iso` (Latest)
   - Click **Open**
4. **Partition scheme**: Select **"GPT"**
5. **Target system**: Select **"UEFI (non CSM)"**
6. **File system**: Leave as **"FAT32"**
7. **Cluster size**: Leave as default
8. Click **"START"**

**Step 5: ISO Image Mode Selection**

- Popup appears: **"Write in ISO Image mode (Recommended)"**
- Click **"OK"**

**Step 6: Warning Confirmation**

- Popup: **"All data on device will be destroyed"**
- Click **"OK"**

**Step 7: Wait for Completion**

- Progress bar shows creation status
- Takes 5-10 minutes
- Status shows **"READY"** when complete

**Step 8: Safely Eject**

1. Click **"CLOSE"** in Rufus
2. Right-click USB drive in File Explorer
3. Select **"Eject"**
4. Remove USB drive

---

## Method 2: Windows (Alternative - balenaEtcher)

**Step 1: Download Ubuntu ISO**
- Same as Method 1 above

**Step 2: Download balenaEtcher**

1. Go to: https://etcher.balena.io/
2. Click **"Download for Windows"**
3. Install `balenaEtcher-Setup.exe`

**Step 3: Create Bootable USB**

1. Launch **balenaEtcher**
2. Click **"Flash from file"**
   - Select `ubuntu-24.04-desktop-amd64.iso`
3. Click **"Select target"**
   - Check your USB drive
   - Click **"Select"**
4. Click **"Flash!"**
5. Enter admin password if prompted
6. Wait for completion (~10 minutes)
7. Click **"Close"** when done

---

## Method 3: Linux (Using dd)

**Step 1: Download Ubuntu ISO**

```bash
cd ~/Downloads
wget https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso
```

**Step 2: Verify Download (Optional)**

```bash
# Download checksums
wget https://releases.ubuntu.com/24.04/SHA256SUMS

# Verify ISO integrity
sha256sum -c SHA256SUMS 2>&1 | grep ubuntu-24.04-desktop-amd64.iso
# Should output: ubuntu-24.04-desktop-amd64.iso: OK
```

**Step 3: Identify USB Drive**

```bash
# Insert USB drive, then check devices
lsblk

# Example output:
# sdb           8:16   1  14.9G  0 disk 
# └─sdb1        8:17   1  14.9G  0 part /media/user/USB_NAME

# Your USB is likely /dev/sdb (NOT /dev/sdb1)
```

**⚠️ CRITICAL:** Make sure you identify the correct device! Using wrong device will destroy data.

**Step 4: Unmount USB (if mounted)**

```bash
# Unmount all partitions on USB
sudo umount /dev/sdb*
```

**Step 5: Write ISO to USB**

```bash
# Write ISO to USB (replace /dev/sdb with your USB device)
sudo dd if=~/Downloads/ubuntu-24.04-desktop-amd64.iso of=/dev/sdb bs=4M status=progress oflag=sync

# This takes 10-15 minutes
# Shows progress as it writes
```

**Step 6: Sync and Eject**

```bash
# Ensure all data written
sync

# Eject USB
sudo eject /dev/sdb
```

---

## Method 4: macOS (Using balenaEtcher)

**Step 1: Download Ubuntu ISO**

1. Go to: https://ubuntu.com/download/desktop
2. Download `ubuntu-24.04-desktop-amd64.iso`

**Step 2: Download balenaEtcher**

1. Go to: https://etcher.balena.io/
2. Click **"Download for macOS"**
3. Open downloaded `.dmg` file
4. Drag balenaEtcher to Applications

**Step 3: Create Bootable USB**

1. Insert USB drive
2. Launch **balenaEtcher** from Applications
3. Click **"Flash from file"**
   - Select `ubuntu-24.04-desktop-amd64.iso`
4. Click **"Select target"**
   - Select your USB drive
5. Click **"Flash!"**
6. Enter Mac password if prompted
7. Wait for completion
8. Eject USB when done

---

## Verify Bootable USB Created Successfully

### On Windows:
1. Open File Explorer
2. USB should appear as **"Ubuntu 24.04 LTS"** or **"Ubuntu 25.10"**
3. Should contain folders: `boot`, `casper`, `dists`, etc.

### On Linux/Mac:
```bash
# List USB contents (adjust version number)
ls /media/$USER/Ubuntu*/
# Should show: boot  casper  dists  install  ...
```

---

## Next Steps: Install Ubuntu on Your Server

### Step 1: Prepare Server

1. **Backup any existing data** on server
2. Ensure RTX 5090 is installed
3. Connect keyboard, mouse, monitor to server
4. Have internet cable ready (Ethernet recommended)

### Step 2: Boot from USB

1. **Insert USB** into server
2. **Power on** server
3. **Press Boot Menu Key** immediately (repeatedly)
   - Common keys: **F12**, **F11**, **F10**, **F8**, **ESC**
   - Depends on your motherboard manufacturer
   - Check screen for "Boot Menu" hint
4. **Select USB drive** from boot menu
   - Look for your USB drive name or "UEFI USB"
5. Press **Enter**

### Step 3: Start Ubuntu Installer

1. Ubuntu boot menu appears
2. Select **"Try or Install Ubuntu"**
3. Wait for Ubuntu to load (~1-2 minutes)

### Step 4: Connect to Internet

1. Click network icon (top-right)
2. Connect to Wi-Fi or plug in Ethernet cable
3. Test connection: Open Firefox, visit google.com

### Step 5: Start Installation

1. Double-click **"Install Ubuntu"** icon on desktop
2. **Language**: Select your language → **Continue**
3. **Keyboard**: Select layout → **Continue**
4. **Updates**: Select **"Normal installation"**
   - ✅ Download updates while installing
   - ✅ Install third-party software (for NVIDIA drivers)
   - **Continue**
5. **Installation type**:
   - **Option A - Erase disk** (recommended for new server):
     - Select **"Erase disk and install Ubuntu"**
     - **Install Now**
   - **Option B - Custom partitions** (advanced):
     - Select **"Something else"** for manual partitioning
6. **Warning prompt**: Review changes → **Continue**

### Step 6: Set Up User Account

1. **Time zone**: Select your location → **Continue**
2. **User information**:
   - Your name: `Your Name`
   - Computer name: `ai-server` (or preferred name)
   - Username: `yourname`
   - Password: Choose strong password
   - Confirm password
   - Select **"Require my password to log in"**
   - **Continue**

### Step 7: Wait for Installation

- Installation takes **20-40 minutes**
- Progress bar shows status
- Downloads updates during installation
- Don't interrupt or power off!

### Step 8: Complete Installation

1. **Installation Complete** dialog appears
2. Click **"Restart Now"**
3. Remove USB drive when prompted
4. Press **Enter**
5. Server reboots into Ubuntu 24.04

### Step 9: First Boot

1. Login with your password
2. Complete welcome screens (optional tutorials)
3. System is ready!

---

## Post-Installation: Install AI Server

**Now run the one-click installer:**

```bash
# Open Terminal (Ctrl+Alt+T)

# Download installer
wget https://raw.githubusercontent.com/lightninglily/LLM/main/local-ai-server/one-click-install.sh

# Make executable
chmod +x one-click-install.sh

# Run installer
./one-click-install.sh

# Wait 30-90 minutes for complete AI server setup
```

---

## Troubleshooting

### USB Not Booting

**Issue**: Server boots to existing OS instead of USB

**Solutions:**
1. Try different boot menu key (F12, F11, F10, ESC)
2. Disable **Secure Boot** in BIOS/UEFI:
   - Restart → Press **Del** or **F2** during boot
   - Find **Secure Boot** setting
   - Change to **Disabled**
   - Save and exit
3. Enable **USB Boot** in BIOS:
   - Check boot order
   - Move USB to first position

### ISO Verification Failed

**Issue**: SHA256 checksum doesn't match

**Solutions:**
1. Re-download ISO (download may be corrupted)
2. Download from different mirror
3. Check internet connection stability

### USB Drive Not Recognized

**Issue**: Rufus or Etcher doesn't see USB drive

**Solutions:**
1. Try different USB port (use USB 2.0 if available)
2. Try different USB drive
3. Format USB first:
   - Windows: Right-click → Format → FAT32
   - Then retry creating bootable USB

### Installation Fails on Server

**Issue**: Ubuntu installer crashes or freezes

**Solutions:**
1. Check RAM: Run memory test from USB boot menu
2. Check disk: Try different drive if available
3. Try "Safe Graphics" mode from boot menu
4. Disconnect unnecessary peripherals during install

---

## Quick Reference

### Recommended Tools:
- **Windows**: Rufus (https://rufus.ie/)
- **macOS**: balenaEtcher (https://etcher.balena.io/)
- **Linux**: `dd` command (built-in)

### Ubuntu Downloads:

**24.04 LTS (Recommended for Servers):**
- **Direct**: https://ubuntu.com/download/desktop
- **Torrent**: https://ubuntu.com/download/alternative-downloads
- **Size**: ~5.7GB
- **Checksum**: https://releases.ubuntu.com/24.04/SHA256SUMS
- **Support**: Until April 2029

**25.10 (Latest Features):**
- **Direct**: https://ubuntu.com/download/desktop
- **Torrent**: https://ubuntu.com/download/alternative-downloads  
- **Size**: ~5.9GB
- **Checksum**: https://releases.ubuntu.com/25.10/SHA256SUMS
- **Support**: Until July 2026

### Common Boot Menu Keys:
| Manufacturer | Boot Menu Key |
|--------------|---------------|
| Dell         | F12           |
| HP           | F9 or ESC     |
| Lenovo       | F12           |
| Asus         | F8 or ESC     |
| Acer         | F12           |
| MSI          | F11           |
| Gigabyte     | F12           |
| Generic      | F12 or ESC    |

### BIOS/UEFI Keys:
| Manufacturer | BIOS Key      |
|--------------|---------------|
| Dell         | F2            |
| HP           | F10 or ESC    |
| Lenovo       | F1 or F2      |
| Asus         | Del or F2     |
| Acer         | F2 or Del     |
| MSI          | Del           |
| Gigabyte     | Del           |
| Generic      | Del or F2     |

---

## Summary

**Creating Ubuntu bootable USB:**

1. ✅ Choose version: 24.04 LTS (recommended) or 25.10 (latest)
2. ✅ Download Ubuntu ISO (~5.7-5.9GB)
3. ✅ Download Rufus (Windows) or balenaEtcher (Mac)
4. ✅ Insert USB drive (8GB+)
5. ✅ Create bootable USB (~10 minutes)
6. ✅ Boot server from USB
7. ✅ Install Ubuntu (~30 minutes)
8. ✅ Run one-click AI installer (~60 minutes)

**Total time:** ~2 hours from blank server to working AI system

**Your AI server will be ready with:**
- Ubuntu 24.04 LTS or 25.10
- NVIDIA drivers (automatically installed)
- Docker + GPU support
- All 4 AI interfaces
- Qwen3-32B model
- Ready to use!

**Both Ubuntu versions work perfectly with our one-click installer!**

---

## Need Help?

**Resources:**
- Ubuntu installation guide: https://ubuntu.com/tutorials/install-ubuntu-desktop
- Rufus documentation: https://github.com/pbatard/rufus/wiki
- AI Server GitHub: https://github.com/lightninglily/LLM

**Common issues solved in this guide:**
- ✅ Creating bootable USB on any OS
- ✅ BIOS/UEFI boot configuration
- ✅ Installation troubleshooting
- ✅ Post-install AI server setup
