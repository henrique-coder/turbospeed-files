# 🚀 TurboSpeed Files

A high-performance file generation system that creates empty binary files of specified sizes for testing, benchmarking, and development purposes.

## ✨ Features

- **📏 Intelligent Size Parsing**: Accepts any format humanfriendly understands (kb, mb, gb, KB, MB, GB, etc.)
- **🧠 Smart Validation**: Prevents duplicates and enforces preferred size formats
- **🤖 Automated Workflow**: Only runs when configuration changes, with intelligent cleanup
- **🗑️ Auto Cleanup**: Removes outdated files from releases automatically
- **📦 Smart Release Management**: Maintains clean, organized releases
- **🔐 Integrity Checking**: Generates MD5 checksums for all files
- **⚡ Optimized Generation**: Fast file creation with duplicate detection

## 📋 Size Limits & Formats

- **Minimum size**: `1kb`
- **Maximum size**: `2gb`
- **Accepted formats**: Any format supported by humanfriendly library
- **Preferred formats**: Use `kb` for <1MB, `mb` for <1GB, `gb` for ≥1GB

## 🚀 Quick Start

1. **Fork this repository**
2. **Edit `file-sizes.yaml`**:

3. **Commit and push** - Actions only run when config changes!

## ⚠️ Format Rules

### ✅ Valid Examples

- `1kb`, `250kb`, `1mb`, `10mb`, `1gb`, `1.5gb`

### ❌ Will Cause Errors

- `0.1mb` (use `100kb` instead)
- `1000kb` (use `1mb` instead)
- `1024mb` (use `1gb` instead)
- Duplicate sizes: `["100kb", "0.1mb"]` (same size, different format)

## 🔧 File Naming

Files are named as: `turbospeed-file-{size}.bin`

## 📄 License

MIT License - Use freely for testing and development.
