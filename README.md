# 🚀 TurboSpeed Files

A high-performance file generation system that creates empty binary files of specified sizes for testing, benchmarking, and development purposes.

## ✨ Features

- **📏 Flexible Size Format**: Supports `{number}mb` and `{number}gb` with float precision
- **🤖 Automated Workflow**: GitHub Actions automatically generates files when configuration changes
- **📦 Smart Release Management**: Automatically manages GitHub releases with proper asset organization
- **🔍 Validation System**: Built-in validation for size limits and configuration format
- **⚡ Optimized Generation**: Fast file creation using chunked writing for large files
- **🛡️ Error Handling**: Comprehensive error checking and limit enforcement
- **📊 Release Tables**: Beautiful tables with download links, sizes, and MD5 hashes

## 📋 GitHub Free Limits

- **Maximum file size**: `2gb` per file
- **Maximum assets per release**: `1000` files
- **Total release size**: No limit

## 🚀 Quick Start

1. **Fork this repository**
2. **Edit `file-sizes.yaml`** with your desired file sizes:

3. **Commit and push** - GitHub Actions will automatically generate files!

## 📝 Configuration Format

### ✅ Valid Formats

- `1mb`, `10mb`, `500mb`
- `1gb`, `1.5gb`, `2gb`
- `0.5mb`, `2.25gb`

### 📏 Size Limits

- **Minimum**: `0.1mb`
- **Maximum**: `2gb`
- **Format**: Must be `{number}mb` or `{number}gb`

## 🔧 File Naming Convention

Files are named as: `turbospeed-file-{size}.bin`

Examples:

- `turbospeed-file-1mb.bin`
- `turbospeed-file-1.5gb.bin`
- `turbospeed-file-2gb.bin`

## 📄 License

MIT License - Use freely for testing and development.
