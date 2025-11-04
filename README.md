# 🚀 TurboSpeed Files

A high-performance file generation system that creates empty binary files of specified sizes for testing, benchmarking, and development purposes.

## ✨ Features

- **📏 Intelligent Size Parsing**: Accepts standard size formats (kb, mb, gb)
- **🧠 Smart Validation**: Prevents duplicates and enforces preferred size formats
- **🤖 Automated Workflow**: Only runs when configuration changes, with intelligent cleanup
- **🗑️ Auto Cleanup**: Removes outdated files from releases automatically
- **📦 Smart Release Management**: Maintains clean, organized releases
- **🔐 Integrity Checking**: Generates MD5 checksums for all files
- **⚡ Optimized Generation**: Fast file creation with duplicate detection
- **🌐 Direct Downloads**: URLs like `henrique-coder.github.io/turbospeed-files/1.5gb` automatically download files

## 📋 Size Limits & Formats

- **Minimum size**: `1kb`
- **Maximum size**: `2gb`
- **Accepted formats**: `kb`, `mb`, `gb` (e.g., `1.5gb`, `100mb`, `50kb`)
- **Preferred formats**: Use `kb` for <1MB, `mb` for <1GB, `gb` for ≥1GB

## 🚀 Quick Start

1. **Fork this repository**
2. **Edit `file_sizes.json`**:
   ```json
   {
     "project_name": "turbospeed",
     "files": ["1kb", "10mb", "100mb", "1gb"]
   }
   ```
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

Files are named as: `{size}.bin` (e.g., `1.5gb.bin`, `100mb.bin`, `1kb.bin`)

## 📄 License

MIT License - Use freely for testing and development.
