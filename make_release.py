import os
import subprocess
import zipfile
import shutil

def make_release():
    print("=== SPHY Model Release Builder ===")
    version = input("Enter the version number for this release (e.g., 1.2): ").strip()
    
    # 1. Define Paths (Releases folder is now inside sphy-gui)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    releases_dir = os.path.abspath(os.path.join(base_dir, "Releases", f"v{version}"))
    src_dir = os.path.join(base_dir, "src")
    
    # Default Inno Setup installation path
    iscc_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    
    if not os.path.exists(iscc_path):
        print(f"\n❌ Error: Could not find Inno Setup at {iscc_path}")
        input("Press Enter to exit...")
        return

    # 2. Run the Build Workspace Script First
    print("\n[1/4] Preparing workspace (running build_workspace_micromamba.py)...")
    build_script = os.path.join(base_dir, "build_workspace_micromamba.py")
    if os.path.exists(build_script):
        try:
            subprocess.run(["python", build_script], check=True)
        except subprocess.CalledProcessError:
            print("\n❌ Error: build_workspace_micromamba.py failed. Halting release build.")
            return
    else:
        print(f"\n⚠️ Warning: {build_script} not found. Skipping workspace build.")

    # 3. Create the Releases directory inside sphy-gui
    os.makedirs(releases_dir, exist_ok=True)
    print(f"\n[2/4] Created release folder: {releases_dir}")
    
    # 4. Zip the source code for archiving
    zip_path = os.path.join(releases_dir, f"src_archive_v{version}.zip")
    print(f"[3/4] Archiving source code to {zip_path}...")
    
    # Folders and file extensions to exclude from the source snapshot
    exclude_dirs = {'.git', 'Releases', 'SPHY_Installer_Build', 'env', '.venv', '__pycache__', '.vscode'}
    exclude_exts = {'.exe', '.pyc', '.zip'}

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Prune excluded directories in-place so os.walk doesn't recurse into them
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in exclude_exts):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, arcname)

    # 5. Compile the Installers via Command Line
    print("\n[4/4] Compiling Installers with Inno Setup...")
    
    print(f"      -> Building SPHY_Setup_v{version}.exe ...")
    subprocess.run([
        iscc_path, 
        os.path.join(base_dir, "setup.iss"),
        f'/O{releases_dir}',                 
        f'/FSPHY_Setup_v{version}',          
        f'/DMyAppVersion={version}'          
    ], check=True)
    
    print(f"      -> Building SPHY_Update_v{version}.exe ...")
    subprocess.run([
        iscc_path, 
        os.path.join(base_dir, "update.iss"),
        f'/O{releases_dir}',                 
        f'/FSPHY_Update_v{version}',         
        f'/DMyAppVersion={version}'          
    ], check=True)

    print(f"\n✅ Success! All files for v{version} are ready in {releases_dir}")
    input("Press Enter to exit...")

if __name__ == "__main__":
    make_release()