#!/usr/bin/env python3

import argparse
import hashlib
import os
from pathlib import Path
import sys
from typing import Any

from humanfriendly import format_size, parse_size
import requests
import yaml


class TurboSpeedGenerator:
    def __init__(self) -> None:
        self.config_file: str = "file-sizes.yaml"
        self.output_dir: Path = Path("./generated")
        self.redirects_dir: Path = Path("./docs/_redirects")
        self.min_file_size_bytes: int = parse_size("1kb")
        self.max_file_size_bytes: int = parse_size("2gb")
        self.max_files_per_release: int = 1000

    def normalize_size_string(self, size_str: str) -> str:
        size_bytes = parse_size(size_str)

        if size_bytes >= parse_size("1gb"):
            gb_value = size_bytes / parse_size("1gb")
            if gb_value == int(gb_value):
                return f"{int(gb_value)}gb"
            else:
                return f"{gb_value:.1f}gb".rstrip("0").rstrip(".")
        elif size_bytes >= parse_size("1mb"):
            mb_value = size_bytes / parse_size("1mb")
            if mb_value == int(mb_value):
                return f"{int(mb_value)}mb"
            else:
                return f"{mb_value:.1f}mb".rstrip("0").rstrip(".")
        else:
            kb_value = size_bytes / parse_size("1kb")
            if kb_value == int(kb_value):
                return f"{int(kb_value)}kb"
            else:
                return f"{kb_value:.1f}kb".rstrip("0").rstrip(".")

    def get_preferred_format(self, size_bytes: int) -> str:
        if size_bytes >= parse_size("1gb"):
            return "gb"
        elif size_bytes >= parse_size("1mb"):
            return "mb"
        else:
            return "kb"

    def parse_and_validate_size(self, size_str: str) -> tuple[int, str]:
        try:
            size_bytes = parse_size(size_str.lower().strip())
        except ValueError as e:
            raise ValueError(f"Invalid size format '{size_str}': {e}") from e

        if size_bytes < self.min_file_size_bytes:
            raise ValueError(f"File size {size_str} is below minimum 100KB")

        if size_bytes > self.max_file_size_bytes:
            raise ValueError(f"File size {size_str} exceeds 2GB limit")

        normalized = self.normalize_size_string(size_str)
        preferred_format = self.get_preferred_format(size_bytes)

        current_format = "gb" if "gb" in normalized else ("mb" if "mb" in normalized else "kb")

        if current_format != preferred_format:
            if preferred_format == "kb":
                suggested = f"{int(size_bytes / parse_size('1kb'))}kb"
            elif preferred_format == "mb":
                suggested = f"{int(size_bytes / parse_size('1mb'))}mb"
            else:
                suggested = f"{size_bytes / parse_size('1gb'):.1f}gb".rstrip("0").rstrip(".")

            raise ValueError(f"Size {size_str} should use preferred format: {suggested}")

        return size_bytes, normalized

    def check_for_duplicates(self, sizes: list[str]) -> None:
        seen_bytes: set[int] = set()
        size_map: dict[int, list[str]] = {}

        for size_str in sizes:
            try:
                size_bytes = parse_size(size_str)
                if size_bytes in seen_bytes:
                    if size_bytes not in size_map:
                        size_map[size_bytes] = []
                    size_map[size_bytes].append(size_str)
                else:
                    seen_bytes.add(size_bytes)
                    size_map[size_bytes] = [size_str]
            except ValueError:
                continue

        duplicates = {k: v for k, v in size_map.items() if len(v) > 1}

        if duplicates:
            error_msg = "Duplicate sizes found:\n"
            for size_bytes, size_strs in duplicates.items():
                preferred = self.normalize_size_string(size_strs[0])
                error_msg += f"  - {', '.join(size_strs)} (all equal {format_size(size_bytes)}) - use: {preferred}\n"
            raise ValueError(error_msg.strip())

    def calculate_md5(self, file_path: Path) -> str:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def load_config(self) -> dict[str, Any]:
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")

        with open(self.config_file) as f:
            config = yaml.safe_load(f)

        if not config or "files" not in config:
            raise ValueError("Invalid configuration: 'files' key missing")

        return config

    def validate_config_silent(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        config = self.load_config()

        if len(config["files"]) > self.max_files_per_release:
            raise ValueError(f"Too many files: {len(config['files'])} > {self.max_files_per_release}")

        self.check_for_duplicates(config["files"])

        validated_files = []

        for size_str in config["files"]:
            size_bytes, normalized_size = self.parse_and_validate_size(size_str)

            validated_files.append({
                "size_str": normalized_size,
                "bytes": size_bytes,
                "filename": f"turbospeed-file-{normalized_size}.bin",
            })

        validated_files.sort(key=lambda x: x["bytes"])

        return config, validated_files

    def validate_config(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        config, validated_files = self.validate_config_silent()

        total_size_bytes = sum(f["bytes"] for f in validated_files)

        print("✅ Configuration valid:")
        print(f"   - Files: {len(validated_files)}")
        print(f"   - Total size: {format_size(total_size_bytes)}")

        return config, validated_files

    def get_release_assets(self) -> list[str]:
        token = os.environ.get("GITHUB_TOKEN")
        repo = os.environ.get("GITHUB_REPOSITORY")
        tag = os.environ.get("RELEASE_TAG", "turbospeed-files")

        if not token or not repo:
            return []

        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
        headers = {"Authorization": f"token {token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                release_data = response.json()
                return [asset["name"] for asset in release_data.get("assets", [])]
        except Exception as e:
            print(f"Warning: Could not fetch release assets: {e}")

        return []

    def get_release_asset_info(self) -> dict[str, dict[str, Any]]:
        token = os.environ.get("GITHUB_TOKEN")
        repo = os.environ.get("GITHUB_REPOSITORY")
        tag = os.environ.get("RELEASE_TAG", "turbospeed-files")

        if not token or not repo:
            return {}

        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
        headers = {"Authorization": f"token {token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                release_data = response.json()
                asset_info = {}
                for asset in release_data.get("assets", []):
                    asset_info[asset["name"]] = {"size": asset["size"], "url": asset["browser_download_url"]}
                return asset_info
        except Exception as e:
            print(f"Warning: Could not fetch release asset info: {e}")

        return {}

    def delete_release_asset(self, asset_name: str) -> bool:
        token = os.environ.get("GITHUB_TOKEN")
        repo = os.environ.get("GITHUB_REPOSITORY")
        tag = os.environ.get("RELEASE_TAG", "turbospeed-files")

        if not token or not repo:
            return False

        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
        headers = {"Authorization": f"token {token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                release_data = response.json()
                for asset in release_data.get("assets", []):
                    if asset["name"] == asset_name:
                        delete_url = asset["url"]
                        delete_response = requests.delete(delete_url, headers=headers)
                        return delete_response.status_code == 204
        except Exception as e:
            print(f"Warning: Could not delete asset {asset_name}: {e}")

        return False

    def clean_release_assets(self) -> None:
        try:
            config, validated_files = self.validate_config_silent()
            valid_filenames = {f["filename"] for f in validated_files}
            valid_filenames.add("checksums.txt")

            current_assets = self.get_release_assets()

            for asset_name in current_assets:
                if asset_name not in valid_filenames:
                    print(f"🗑️  Removing outdated asset: {asset_name}")
                    self.delete_release_asset(asset_name)

        except Exception as e:
            print(f"Warning: Could not clean release assets: {e}")

    def check_missing_files(self) -> list[dict[str, Any]]:
        try:
            config, validated_files = self.validate_config_silent()
            release_assets = self.get_release_asset_info()

            missing_files = []

            for file_info in validated_files:
                filename = file_info["filename"]
                expected_size = file_info["bytes"]

                if filename not in release_assets:
                    missing_files.append(file_info)
                    print(f"🔍 Missing file: {filename}")
                elif release_assets[filename]["size"] != expected_size:
                    missing_files.append(file_info)
                    print(
                        f"🔍 Size mismatch: {filename} (expected: {format_size(expected_size)}, got: {format_size(release_assets[filename]['size'])})"
                    )

            if not missing_files:
                print("✅ All required files exist in release with correct sizes")
            else:
                print(f"⚠️  Found {len(missing_files)} files that need to be updated")

            return missing_files

        except Exception as e:
            print(f"Warning: Could not check missing files: {e}")
            return []

    def sync_release_assets(self) -> None:
        print("🔄 Syncing release assets...")

        self.clean_release_assets()

        missing_files = self.check_missing_files()

        if missing_files:
            print(f"📋 {len(missing_files)} files need to be generated")

        print("✅ Release sync completed")

    def create_file_optimized(self, file_path: Path, size_bytes: int) -> None:
        chunk_size = min(1024 * 1024, size_bytes)

        with open(file_path, "wb") as f:
            remaining = size_bytes

            while remaining > 0:
                write_size = min(chunk_size, remaining)
                f.write(b"\0" * write_size)
                remaining -= write_size

    def generate_files(self) -> None:
        config, validated_files = self.validate_config_silent()

        release_assets = self.get_release_asset_info()
        files_to_generate = []

        for file_info in validated_files:
            filename = file_info["filename"]
            expected_size = file_info["bytes"]

            if filename not in release_assets or release_assets[filename]["size"] != expected_size:
                files_to_generate.append(file_info)

        if not files_to_generate:
            print("✅ All files exist in release with correct sizes - nothing to generate")
            return

        print(f"🚀 Generating {len(files_to_generate)} missing/incorrect files...")

        self.output_dir.mkdir(exist_ok=True)

        for file_info in files_to_generate:
            filename = file_info["filename"]
            size_bytes = file_info["bytes"]
            file_path = self.output_dir / filename

            print(f"   Creating {filename} ({format_size(size_bytes)})...")
            self.create_file_optimized(file_path, size_bytes)

        print(f"✅ Generated {len(files_to_generate)} files successfully!")

    def generate_checksums(self) -> None:
        config, validated_files = self.validate_config_silent()

        if not self.output_dir.exists():
            print("⚠️  No local files found - skipping checksums generation")
            return

        checksums_path = self.output_dir / "checksums.txt"
        local_files = list(self.output_dir.glob("*.bin"))

        if not local_files:
            print("⚠️  No .bin files found locally - skipping checksums")
            return

        print(f"🔐 Generating checksums for {len(local_files)} local files...")

        with open(checksums_path, "w") as f:
            for file_path in sorted(local_files):
                if file_path.is_file():
                    md5_hash = self.calculate_md5(file_path)
                    f.write(f"{md5_hash}  {file_path.name}\n")
                    print(f"   {file_path.name}: {md5_hash}")

        print(f"✅ Checksums saved to {checksums_path}")

    def generate_jekyll_redirects(self) -> None:
        config, validated_files = self.validate_config_silent()

        self.redirects_dir.mkdir(exist_ok=True, parents=True)

        repo = os.environ.get("GITHUB_REPOSITORY", "henrique-coder/turbospeed-files")

        print("🔗 Generating Jekyll redirect pages...")

        for file_info in validated_files:
            size_str = file_info["size_str"]
            filename = file_info["filename"]

            redirect_url = f"https://github.com/{repo}/releases/download/turbospeed-files/{filename}"

            redirect_content = f"""---
layout: redirect
redirect_to: {redirect_url}
permalink: /{size_str}/
---
"""

            redirect_file = self.redirects_dir / f"{size_str}.md"
            with open(redirect_file, "w") as f:
                f.write(redirect_content)

            print(f"   Created redirect: /{size_str}/ -> {filename}")

        print("✅ Jekyll redirects generated successfully!")

    def generate_release_table(self) -> str:
        try:
            config, validated_files = self.validate_config_silent()
            # release_assets = self.get_release_asset_info()

            table_header = "| File | Size | Hash (MD5) | Download |\n|------|------|------------|----------|\n"
            table_rows = []

            repo_full = os.environ.get("GITHUB_REPOSITORY", "user/repo")
            repo_owner = repo_full.split("/")[0]

            for file_info in validated_files:
                filename = file_info["filename"]
                size_human = format_size(file_info["bytes"])
                size_only = file_info["size_str"]
                download_url = f"https://{repo_owner}.github.io/turbospeed-files/{size_only}"

                file_path = self.output_dir / filename
                md5_hash = self.calculate_md5(file_path) if file_path.exists() else "updating..."

                row = f"| `{filename}` | **{size_human}** | `{md5_hash}` | [📥 Download]({download_url}) |"
                table_rows.append(row)

            if not table_rows:
                return "No files configured."

            total_size = sum(f["bytes"] for f in validated_files)
            release_tag = os.environ.get("RELEASE_TAG", "turbospeed-files")
            footer = f"\n\n**Total Collection Size:** {format_size(total_size)} • **Files:** {len(table_rows)}\n\n**Checksums:** [📋 checksums.txt](https://github.com/{repo_full}/releases/download/{release_tag}/checksums.txt)"

            return table_header + "\n".join(table_rows) + footer

        except Exception as e:
            return f"Error generating table: {str(e)}"

    def calculate_total_size(self) -> str:
        try:
            config, validated_files = self.validate_config_silent()
            total_bytes = sum(f["bytes"] for f in validated_files)
            return format_size(total_bytes)
        except Exception:
            return "Unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="TurboSpeed Files Generator")
    parser.add_argument("--validate", action="store_true", help="Validate configuration only")
    parser.add_argument("--generate", action="store_true", help="Generate missing files only")
    parser.add_argument("--calculate-total", action="store_true", help="Calculate total size")
    parser.add_argument("--generate-table", action="store_true", help="Generate release table")
    parser.add_argument("--generate-checksums", action="store_true", help="Generate checksums file")
    parser.add_argument("--clean-release", action="store_true", help="Clean outdated release assets")
    parser.add_argument("--sync-release", action="store_true", help="Sync release assets (clean + check missing)")
    parser.add_argument("--generate-jekyll-redirects", action="store_true", help="Generate Jekyll redirect pages")

    args = parser.parse_args()
    generator = TurboSpeedGenerator()

    try:
        if args.validate:
            generator.validate_config()
        elif args.generate:
            generator.generate_files()
        elif args.calculate_total:
            print(generator.calculate_total_size())
        elif args.generate_table:
            print(generator.generate_release_table())
        elif args.generate_checksums:
            generator.generate_checksums()
        elif args.clean_release:
            generator.clean_release_assets()
        elif args.sync_release:
            generator.sync_release_assets()
        elif args.generate_jekyll_redirects:
            generator.generate_jekyll_redirects()
        else:
            parser.print_help()

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
