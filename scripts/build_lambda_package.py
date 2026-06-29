"""Build the AWS Lambda deployment zip with handler files at the zip root."""

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAMBDA_DIR = PROJECT_ROOT / "lambda"
BUILD_DIR = PROJECT_ROOT / "package"
OUTPUT_ZIP = PROJECT_ROOT / "lambda_deployment_package.zip"
REQUIRED_ROOT_FILES = {
    "lambda_function.py",
    "transformations.py",
    "utils.py",
}


def install_dependencies(requirements_file, target_dir):
    if not requirements_file.exists() or not requirements_file.read_text(encoding="utf-8").strip():
        return

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_file),
            "-t",
            str(target_dir),
        ]
    )


def copy_lambda_sources(target_dir):
    for source_file in LAMBDA_DIR.glob("*.py"):
        if source_file.name == "__init__.py":
            continue

        shutil.copy2(source_file, target_dir / source_file.name)


def create_zip(source_dir, output_zip):
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                zip_file.write(file_path, file_path.relative_to(source_dir))


def verify_zip(output_zip):
    with zipfile.ZipFile(output_zip) as zip_file:
        names = set(zip_file.namelist())

    missing = REQUIRED_ROOT_FILES - names

    if missing:
        missing_files = ", ".join(sorted(missing))
        raise RuntimeError(f"Invalid Lambda package. Missing files at zip root: {missing_files}")

    nested_handler = "lambda/lambda_function.py"

    if nested_handler in names:
        raise RuntimeError(
            "Invalid Lambda package. lambda_function.py is nested under lambda/ instead of the zip root."
        )


def build_package(install_deps=False):
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    BUILD_DIR.mkdir(parents=True)

    if install_deps:
        install_dependencies(LAMBDA_DIR / "requirements.txt", BUILD_DIR)

    copy_lambda_sources(BUILD_DIR)
    create_zip(BUILD_DIR, OUTPUT_ZIP)
    verify_zip(OUTPUT_ZIP)

    return OUTPUT_ZIP


def main():
    parser = argparse.ArgumentParser(description="Build Lambda deployment package.")
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install lambda/requirements.txt into the deployment package.",
    )
    args = parser.parse_args()

    output_zip = build_package(install_deps=args.install_deps)
    print(f"Built {output_zip}")
    print("AWS Lambda handler: lambda_function.lambda_handler")


if __name__ == "__main__":
    main()
