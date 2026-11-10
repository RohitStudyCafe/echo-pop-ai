import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

def build_package():
    workspace = Path(__file__).parent.parent
    build_dir = workspace / "build_lambda"
    zip_output = workspace / "lambda_deployment_package.zip"

    print("--> Cleaning prior build artifacts...")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if zip_output.exists():
        zip_output.unlink()

    build_dir.mkdir(parents=True, exist_ok=True)

    print("--> Installing Linux-compatible dependencies for Python 3.12...")
    lambda_reqs = [
        "fastapi==0.110.0",
        "pydantic==2.6.4",
        "pydantic-settings==2.2.1",
        "httpx==0.27.0",
        "mangum==0.22.0"
    ]
    
    req_file = build_dir / "lambda_requirements.txt"
    req_file.write_text("\n".join(lambda_reqs))

    cmd = [
        sys.executable, "-m", "pip", "install",
        "-r", str(req_file),
        "-t", str(build_dir),
        "--platform", "manylinux2014_x86_64",
        "--python-version", "3.12",
        "--only-binary=:all:",
        "--no-compile"
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Warning: pip cross-platform install returned non-zero. Falling back to local wheel copy...")
        # fallback to standard target install
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file), "-t", str(build_dir)], check=True)

    # Remove temporary requirements file
    if req_file.exists():
        req_file.unlink()

    print("--> Copying application source code...")
    app_src = workspace / "app"
    shutil.copytree(app_src, build_dir / "app")

    print(f"--> Creating {zip_output.name}...")
    with zipfile.ZipFile(zip_output, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(build_dir)
                zf.write(file_path, arcname)

    size_mb = zip_output.stat().st_size / (1024 * 1024)
    print(f"✅ Success! Created {zip_output} ({size_mb:.2f} MB)")
    print("You can upload this ZIP directly to the AWS Lambda Console.")

if __name__ == "__main__":
    build_package()

