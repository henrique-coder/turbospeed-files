import argparse
import hashlib
import os
from pathlib import Path
import sys
from typing import Any

from humanfriendly import format_size, parse_size
import yaml


class TurboSpeedGenerator:
    def __init__(self) -> None:
        self.config_file: str = "file-sizes.yaml"
        self.output_dir: Path = Path("./generated")
        self.max_file_size_bytes: int = 2 * 1024 * 1024 * 1024
        self.max_files_per_release: int = 1000

    def parse_and_validate_size(self, size_str: str) -> tuple[int, str]:
        normalized_size = size_str.lower().strip()

        try:
            size_bytes = parse_size(normalized_size)
        except ValueError as e:
            raise ValueError(f"Invalid size format '{size_str}': {e}") from e

        if size_bytes > self.max_file_size_bytes:
            raise ValueError(f"File size {size_str} exceeds 2GB limit")

        if size_bytes < parse_size("0.1MB"):
            raise ValueError(f"File size {size_str} is below minimum 0.1MB")

        return size_bytes, normalized_size

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

    def validate_config(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        config = self.load_config()

        if len(config["files"]) > self.max_files_per_release:
            raise ValueError(f"Too many files: {len(config['files'])} > {self.max_files_per_release}")

        total_size_bytes = 0
        validated_files = []
        seen_sizes = set()

        for size_str in config["files"]:
            size_bytes, normalized_size = self.parse_and_validate_size(size_str)

            if normalized_size in seen_sizes:
                raise ValueError(f"Duplicate size found: {size_str}")

            seen_sizes.add(normalized_size)
            total_size_bytes += size_bytes

            validated_files.append({
                "size_str": normalized_size,
                "bytes": size_bytes,
                "filename": f"turbospeed-file-{normalized_size}.bin",
            })

        validated_files.sort(key=lambda x: x["bytes"])

        print("✅ Configuration valid:")
        print(f"   - Files: {len(validated_files)}")
        print(f"   - Total size: {format_size(total_size_bytes)}")

        return config, validated_files

    def create_file_optimized(self, file_path: Path, size_bytes: int) -> None:
        chunk_size = min(1024 * 1024, size_bytes)

        with open(file_path, "wb") as f:
            remaining = size_bytes

            while remaining > 0:
                write_size = min(chunk_size, remaining)
                f.write(b"\0" * write_size)
                remaining -= write_size

    def generate_files(self) -> None:
        config, validated_files = self.validate_config()

        self.output_dir.mkdir(exist_ok=True)

        existing_files = {f.name for f in self.output_dir.glob("*.bin")}

        print(f"🚀 Generating {len(validated_files)} files...")

        for file_info in validated_files:
            filename = file_info["filename"]
            size_bytes = file_info["bytes"]
            file_path = self.output_dir / filename

            if filename in existing_files and file_path.stat().st_size == size_bytes:
                print(f"   Skipping {filename} (already exists)")
                continue

            print(f"   Creating {filename} ({format_size(size_bytes)})...")
            self.create_file_optimized(file_path, size_bytes)

        print(f"✅ Generated {len(validated_files)} files successfully!")

    def generate_release_table(self) -> str:
        try:
            config, validated_files = self.validate_config()

            if not self.output_dir.exists():
                return "No files generated yet."

            table_header = "| File | Size | Hash (MD5) | Download |\n|------|------|------------|----------|\n"
            table_rows = []

            repo_name = os.environ.get("GITHUB_REPOSITORY", "user/repo")
            release_tag = os.environ.get("RELEASE_TAG", "turbospeed-files")

            for file_info in validated_files:
                filename = file_info["filename"]
                file_path = self.output_dir / filename

                if file_path.exists():
                    size_human = format_size(file_info["bytes"])
                    md5_hash = self.calculate_md5(file_path)[:8] + "..."
                    download_url = f"https://github.com/{repo_name}/releases/download/{release_tag}/{filename}"

                    row = f"| `{filename}` | **{size_human}** | `{md5_hash}` | [📥 Download]({download_url}) |"
                    table_rows.append(row)

            if not table_rows:
                return "No files available for download."

            total_size = sum(f["bytes"] for f in validated_files)
            footer = f"\n**Total Collection Size:** {format_size(total_size)} • **Files:** {len(table_rows)}"

            return table_header + "\n".join(table_rows) + footer

        except Exception as e:
            return f"Error generating table: {str(e)}"

    def calculate_total_size(self) -> str:
        try:
            config, validated_files = self.validate_config()
            total_bytes = sum(f["bytes"] for f in validated_files)
            return format_size(total_bytes)
        except Exception:
            return "Unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="TurboSpeed Files Generator")
    parser.add_argument("--validate", action="store_true", help="Validate configuration only")
    parser.add_argument("--generate", action="store_true", help="Generate files")
    parser.add_argument("--calculate-total", action="store_true", help="Calculate total size")
    parser.add_argument("--generate-table", action="store_true", help="Generate release table")

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
        else:
            parser.print_help()

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
