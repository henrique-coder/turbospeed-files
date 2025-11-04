# 🚀 TurboSpeed Files

Empty binary files for testing and benchmarking.

## Setup

1. Fork this repository
2. Edit `file_sizes.json` with desired file sizes:
   ```json
   ["1kb", "100mb", "1gb", "1.5gb"]
   ```
3. Commit and push

GitHub Actions will automatically generate files and create a release.

## Download

```bash
curl -L -O https://github.com/henrique-coder/turbospeed-files/releases/download/turbospeed-files/100mb.bin
```

## License

MIT
