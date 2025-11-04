import hashlib
import os
from pathlib import Path

import httpx
from humanfriendly import parse_size as hf_parse_size
import humanize
import orjson
import typer


app = typer.Typer(add_completion=False, no_args_is_help=True)

CONFIG_FILE = "file_sizes.json"
OUTPUT_DIR = Path("./generated")
REDIRECTS_DIR = Path("./docs/_redirects")
RELEASE_TAG = "turbospeed-files"


def load_config() -> list[str]:
    if not os.path.exists(CONFIG_FILE):
        typer.echo(f"Error: {CONFIG_FILE} not found", err=True)
        raise typer.Exit(1)

    with open(CONFIG_FILE, "rb") as f:
        data = orjson.loads(f.read())

    if not isinstance(data, list):
        typer.echo("Error: config must be an array of strings", err=True)
        raise typer.Exit(1)

    return [s.strip().replace(" ", "").lower() for s in data]


def parse_size(size_str: str) -> int:
    try:
        return hf_parse_size(size_str)
    except Exception as e:
        typer.echo(f"Error parsing size '{size_str}': {e}", err=True)
        raise typer.Exit(1) from None


def format_size(size_bytes: int) -> str:
    return humanize.naturalsize(size_bytes, binary=True)


def normalize_filename(size_str: str) -> str:
    return size_str.strip().replace(" ", "").lower()


def get_github_api_headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    return {"Accept": "application/vnd.github+json"}


def get_repo() -> str:
    return os.environ.get("GITHUB_REPOSITORY", "henrique-coder/turbospeed-files")


def get_release_info():
    repo = get_repo()
    url = f"https://api.github.com/repos/{repo}/releases/tags/{RELEASE_TAG}"

    try:
        with httpx.Client() as client:
            response = client.get(url, headers=get_github_api_headers(), timeout=30)
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    return None


def delete_asset(asset_id: int) -> bool:
    repo = get_repo()
    url = f"https://api.github.com/repos/{repo}/releases/assets/{asset_id}"

    try:
        with httpx.Client() as client:
            response = client.delete(url, headers=get_github_api_headers(), timeout=30)
            return response.status_code == 204
    except Exception:
        return False


def calculate_md5(file_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_file(file_path: Path, size_bytes: int):
    chunk_size = min(1024 * 1024, size_bytes)
    with open(file_path, "wb") as f:
        remaining = size_bytes
        while remaining > 0:
            write_size = min(chunk_size, remaining)
            f.write(b"\0" * write_size)
            remaining -= write_size


@app.command()
def validate():
    sizes = load_config()

    if len(sizes) > 1000:
        typer.echo(f"Error: too many files ({len(sizes)} > 1000)", err=True)
        raise typer.Exit(1)

    seen = set()
    files_info = []

    for size_str in sizes:
        size_bytes = parse_size(size_str)

        if size_bytes in seen:
            typer.echo(f"Error: duplicate size detected: {size_str}", err=True)
            raise typer.Exit(1)

        seen.add(size_bytes)
        filename = f"{normalize_filename(size_str)}.bin"
        files_info.append((filename, size_bytes))

    total_size = sum(s for _, s in files_info)
    typer.echo(f"✅ Valid: {len(files_info)} files, total {format_size(total_size)}")


@app.command()
def generate():
    sizes = load_config()
    OUTPUT_DIR.mkdir(exist_ok=True)

    typer.echo(f"Generating {len(sizes)} files...")

    for size_str in sizes:
        size_bytes = parse_size(size_str)
        filename = f"{normalize_filename(size_str)}.bin"
        file_path = OUTPUT_DIR / filename

        if file_path.exists() and file_path.stat().st_size == size_bytes:
            typer.echo(f"  ✓ {filename}")
            continue

        typer.echo(f"  Creating {filename} ({format_size(size_bytes)})...")
        create_file(file_path, size_bytes)

    typer.echo("✅ Done")


@app.command()
def checksums():
    if not OUTPUT_DIR.exists():
        typer.echo("No files to checksum", err=True)
        raise typer.Exit(1)

    files = sorted(OUTPUT_DIR.glob("*.bin"))
    if not files:
        typer.echo("No .bin files found", err=True)
        raise typer.Exit(1)

    checksums_path = OUTPUT_DIR / "checksums.txt"

    with open(checksums_path, "w") as f:
        for file_path in files:
            md5 = calculate_md5(file_path)
            f.write(f"{md5}  {file_path.name}\n")
            typer.echo(f"  {file_path.name}: {md5}")

    typer.echo(f"✅ Saved to {checksums_path}")


@app.command()
def redirects():
    sizes = load_config()
    REDIRECTS_DIR.mkdir(exist_ok=True, parents=True)

    repo = get_repo()

    for size_str in sizes:
        normalized = normalize_filename(size_str)
        filename = f"{normalized}.bin"

        redirect_url = f"https://github.com/{repo}/releases/download/{RELEASE_TAG}/{filename}"

        content = f"""---
layout: redirect
redirect_to: {redirect_url}
permalink: /{normalized}/
---
"""

        redirect_file = REDIRECTS_DIR / f"{normalized}.md"
        with open(redirect_file, "w") as f:
            f.write(content)

        typer.echo(f"  /{normalized}/ -> {filename}")

    typer.echo("✅ Redirects created")


@app.command()
def table():
    sizes = load_config()
    repo = get_repo()
    repo_owner = repo.split("/")[0]

    lines = ["| File | Size | Hash (MD5) | Download |", "|------|------|------------|----------|"]

    total_size = 0

    for size_str in sizes:
        size_bytes = parse_size(size_str)
        total_size += size_bytes
        normalized = normalize_filename(size_str)
        filename = f"{normalized}.bin"
        size_human = format_size(size_bytes)
        download_url = f"https://{repo_owner}.github.io/turbospeed-files/{normalized}"

        file_path = OUTPUT_DIR / filename
        md5 = calculate_md5(file_path) if file_path.exists() else "pending"

        lines.append(f"| `{filename}` | **{size_human}** | `{md5}` | [📥 Download]({download_url}) |")

    footer = f"\n\n**Total:** {format_size(total_size)} • **Files:** {len(sizes)}\n\n**Checksums:** [checksums.txt](https://github.com/{repo}/releases/download/{RELEASE_TAG}/checksums.txt)"

    print("\n".join(lines) + footer)


@app.command()
def cleanup():
    release_info = get_release_info()
    if not release_info:
        typer.echo("No release found")
        return

    sizes = load_config()
    valid_filenames = {f"{normalize_filename(s)}.bin" for s in sizes}
    valid_filenames.add("checksums.txt")

    assets = release_info.get("assets", [])
    removed = 0

    for asset in assets:
        name = asset["name"]
        if name not in valid_filenames:
            typer.echo(f"  Removing {name}...")
            if delete_asset(asset["id"]):
                removed += 1
            else:
                typer.echo(f"    Failed to remove {name}", err=True)

    typer.echo(f"✅ Removed {removed} outdated assets")


@app.command()
def run():
    typer.echo("=== Validating ===")
    validate()

    typer.echo("\n=== Generating files ===")
    generate()

    typer.echo("\n=== Creating checksums ===")
    checksums()

    typer.echo("\n=== Generating redirects ===")
    redirects()

    typer.echo("\n=== Cleaning up release ===")
    cleanup()

    typer.echo("\n✅ All done!")


if __name__ == "__main__":
    app()
