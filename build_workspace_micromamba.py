import os
import urllib.request
import tarfile
import io
import shutil

# --- 1. SETUP PATHS ---
base_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(base_dir, 'SPHY_Installer_Build')
src_dir = os.path.join(build_dir, 'src')

# IMPORTANT: Put the exact path to your external SPHY model folder here
sphy_model_source = r"G:\\Otros ordenadores\\Mi PC\\versions\\SPHY-github"
# sphy_model_source = r"c:\\research\\models\\SPHY\\versions\\SPHY-github"

# This is where the model will sit inside the installer folder
sphy_model_dest = os.path.join(src_dir, 'sphy_model')

print("Cleaning old build directories...")
if os.path.exists(build_dir):
    shutil.rmtree(build_dir)
os.makedirs(src_dir)

# --- 2. COPY GUI FILES & FOLDERS ---
files_to_copy = ['main.py', 'icon_GUI.png', 'icon_window.png', 'icon.ico', 'gui_def.yaml', 'license.txt'] # config_gilao.cfg and sphy.py removed
folders_to_copy = ['icons', 'help'] # help folder added

print("Copying GUI files...")
for file in files_to_copy:
    src_file = os.path.join(base_dir, file)
    if os.path.exists(src_file):
        shutil.copy2(src_file, os.path.join(src_dir, file))
    else:
        print(f"Warning: Could not find {file}")

for folder in folders_to_copy:
    src_folder = os.path.join(base_dir, folder)
    if os.path.exists(src_folder):
        shutil.copytree(src_folder, os.path.join(src_dir, folder))
    else:
        print(f"Warning: Could not find {folder}")

# --- 3. COPY EXTERNAL SPHY MODEL (.py files only) ---
print(f"Copying SPHY model scripts from {sphy_model_source}...")
if not os.path.exists(sphy_model_source):
    print(f"ERROR: Cannot find SPHY model folder at {sphy_model_source}")
else:
    for root, dirs, files in os.walk(sphy_model_source):
        # Skip hidden folders like .git to save space
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                # Get absolute path of the source file
                src_file_path = os.path.join(root, file)
                # Calculate its relative path so we can recreate the folder structure
                rel_path = os.path.relpath(src_file_path, sphy_model_source)
                # Create the final destination path inside our build folder
                dest_file_path = os.path.join(sphy_model_dest, rel_path)
                
                # Ensure the subfolder exists before copying
                os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                shutil.copy2(src_file_path, dest_file_path)

# --- 4. GENERATE environment.yml (Name removed to force prefix installation) ---
print("Generating environment.yml...")
env_yml = """channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pcraster
  - numpy
  - pandas
  - scipy
  - netcdf4
  - pyproj
  - qt=5.15
  - pyqt=5.15
  - pyqtchart
  - pip
  - pip:
    - configupdater
    - pyqtdarktheme-fork
    - markdown
    - pyyaml
"""
with open(os.path.join(build_dir, 'environment.yml'), 'w') as f:
    f.write(env_yml)

# --- 5. GENERATE LAUNCHERS, INSTALL SCRIPTS & DOWNLOAD MICROMAMBA ---

print("Downloading Micromamba (10 MB)...")
mamba_url = "https://micro.mamba.pm/api/micromamba/win-64/latest"
req = urllib.request.Request(mamba_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    import io, tarfile # Just making sure these are imported!
    with tarfile.open(fileobj=io.BytesIO(response.read()), mode="r:bz2") as tar:
        for member in tar.getmembers():
            if member.name.endswith("micromamba.exe"):
                member.name = "micromamba.exe" # Extract it directly to the root folder
                
                # --- THE TAR SLIP FIX ---
                # If Python is new enough to support the security filter, use it.
                if hasattr(tarfile, 'data_filter'):
                    tar.extract(member, path=build_dir, filter='data')
                else:
                    # Fallback for older Python versions
                    tar.extract(member, path=build_dir)
                break

print("Generating launch.vbs (The Invisibility Cloak)...")
vbs_script = """Set WshShell = CreateObject("WScript.Shell")
Dim scriptDir
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run chr(34) & scriptDir & "\\run_app.bat" & chr(34), 0
Set WshShell = Nothing
"""
with open(os.path.join(build_dir, 'launch.vbs'), 'w') as f:
    f.write(vbs_script)

print("Generating run_app.bat (The Micromamba Runner)...")
run_bat_script = """@echo off
cd /d "%~dp0"
:: Micromamba is so fast it doesn't even need a separate 'activate' step!
"%~dp0micromamba.exe" run -p "%~dp0env" python "%~dp0src\\main.py"
"""
with open(os.path.join(build_dir, 'run_app.bat'), 'w') as f:
    f.write(run_bat_script)

print("Generating install_env.bat (The Math Engine Downloader)...")
install_bat_script = """@echo off
:: Make the terminal look professional (Blue background, white text)
title SPHY Model - Downloading Environment Dependencies

echo ===================================================
echo   SPHY Model: Downloading Math Libraries...
echo   Please do not close this window!
echo   (This may take 5-10 minutes depending on your
echo   internet connection)
echo ===================================================

set "MAMBA_EXE=%~dp0micromamba.exe"
set "ENV_DIR=%~dp0env"
set "YML_FILE=%~dp0environment.yml"

:: Force auto-accept for all license prompts
set "MICROMAMBA_ALWAYS_YES=true"

:: Create the environment using Micromamba (with -y for auto-yes)
"%MAMBA_EXE%" create -p "%ENV_DIR%" -f "%YML_FILE%" -y

echo.
echo ===================================================
echo CLEANING CACHE...
echo ===================================================
"%MAMBA_EXE%" clean --all -y

echo.
echo ===================================================
echo FINISHED! The installer will now complete.
echo ===================================================
:: We use 'timeout' instead of 'pause' so it closes automatically after 5 seconds!
timeout /t 5 >nul
"""
with open(os.path.join(build_dir, 'install_env.bat'), 'w') as f:
    f.write(install_bat_script)

print(f"\n✅ Success! Workspace ready at: {build_dir}")