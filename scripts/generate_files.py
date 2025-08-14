"""
TurboSpeed Files Generator
Generates empty files with specified sizes for testing purposes.
"""


import os
import sys
import yaml
import argparse
import re
from pathlib import Path


class TurboSpeedGenerator:
    def __init__(self):
        self.config_file = 'file-sizes.yaml'
        self.output_dir = Path('./generated')
        self.max_file_size_gb = 2  # GitHub Free limit
        self.max_files_per_release = 1000  # GitHub limit

    def parse_size(self, size_str):
        """Parse size string like '1.5GB', '500MB' to bytes."""
        pattern = r'^(\d+(?:\.\d+)?)(MB|GB)$'
        match = re.match(pattern, size_str.upper())

        if not match:
            raise ValueError(f"Invalid size format: {size_str}")

        value, unit = match.groups()
        value = float(value)

        if unit == 'MB':
            bytes_size = int(value * 1024 * 1024)
        elif unit == 'GB':
            bytes_size = int(value * 1024 * 1024 * 1024)

        return bytes_size, value, unit

    def validate_config(self):
        """Validate the configuration file."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")

        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)

        if not config or 'files' not in config:
            raise ValueError("Invalid configuration: 'files' key missing")

        if len(config['files']) > self.max_files_per_release:
            raise ValueError(f"Too many files: {len(config['files'])} > {self.max_files_per_release}")

        project_name = config.get('project_name', 'turbospeed')

        total_size_bytes = 0
        validated_files = []

        for size_str in config['files']:
            try:
                bytes_size, value, unit = self.parse_size(size_str)

                # Check individual file size limit
                if unit == 'GB' and value > self.max_file_size_gb:
                    raise ValueError(f"File size {size_str} exceeds {self.max_file_size_gb}GB limit")

                total_size_bytes += bytes_size
                validated_files.append({
                    'size_str': size_str,
                    'bytes': bytes_size,
                    'filename': f"{project_name}-{size_str}.bin"
                })

            except ValueError as e:
                raise ValueError(f"Invalid size '{size_str}': {e}")

        # Sort by size
        validated_files.sort(key=lambda x: x['bytes'])

        print(f"✅ Configuration valid:")
        print(f"   - Files: {len(validated_files)}")
        print(f"   - Total size: {self.format_bytes(total_size_bytes)}")
        print(f"   - Project: {project_name}")

        return config, validated_files

    def format_bytes(self, bytes_size):
        """Format bytes to human readable string."""
        if bytes_size >= 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024 * 1024):.2f}GB"
        elif bytes_size >= 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.2f}MB"
        else:
            return f"{bytes_size / 1024:.2f}KB"

    def generate_files(self):
        """Generate the files specified in configuration."""
        config, validated_files = self.validate_config()

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

        print(f"🚀 Generating {len(validated_files)} files...")

        for file_info in validated_files:
            filename = file_info['filename']
            size_bytes = file_info['bytes']
            file_path = self.output_dir / filename

            print(f"   Creating {filename} ({self.format_bytes(size_bytes)})...")

            # Create empty file with specific size (optimized)
            with open(file_path, 'wb') as f:
                # Write in chunks for better performance
                chunk_size = 1024 * 1024  # 1MB chunks
                remaining = size_bytes

                while remaining > 0:
                    write_size = min(chunk_size, remaining)
                    f.write(b'\0' * write_size)
                    remaining -= write_size

        print(f"✅ Generated {len(validated_files)} files successfully!")

    def calculate_total_size(self):
        """Calculate total size of files in configuration."""
        try:
            config, validated_files = self.validate_config()
            total_bytes = sum(f['bytes'] for f in validated_files)
            return self.format_bytes(total_bytes)
        except Exception:
            return "Unknown"

def main():
    parser = argparse.ArgumentParser(description='TurboSpeed Files Generator')
    parser.add_argument('--validate', action='store_true', help='Validate configuration only')
    parser.add_argument('--generate', action='store_true', help='Generate files')
    parser.add_argument('--calculate-total', action='store_true', help='Calculate total size')

    args = parser.parse_args()
    generator = TurboSpeedGenerator()

    try:
        if args.validate:
            generator.validate_config()
        elif args.generate:
            generator.generate_files()
        elif args.calculate_total:
            print(generator.calculate_total_size())
        else:
            parser.print_help()

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
