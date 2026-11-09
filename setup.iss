#define MyAppName "SPHY_Model"
#define MyAppPublisher "Joris Eekhout/University of Murcia & CEBAS-CSIC"
#define MyAppExeName "launch.vbs"

[Setup]
; --- General Settings ---
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Installing to C:\ to avoid ANY spaces in folder names
DefaultDirName=C:\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
UsePreviousAppDir=no
ExtraDiskSpaceRequired=2541820537
LicenseFile=src\license.txt

; --- Where the installer is built ---
; IMPORTANT: Verify this path points to your build_workspace.py output folder!
; SourceDir=C:\research\data_analysis\python\sphy-gui\SPHY_Installer_Build\
SourceDir=G:\Otros ordenadores\Mi PC\data_analysis\python\sphy-gui\SPHY_Installer_Build\
Compression=lzma
SolidCompression=yes

[Files]
Source: "src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "environment.yml"; DestDir: "{app}"; Flags: ignoreversion
Source: "launch.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "run_app.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_env.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "micromamba.exe"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Icons]
; Creates the Desktop Shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\src\icon.ico"; Tasks: desktopicon
; Creates the Start Menu Shortcut
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\src\icon.ico"

[Run]
Filename: "{app}\install_env.bat"; StatusMsg: "Downloading SPHY dependencies..."; Flags: waituntilterminated

[Registry]
Root: HKCU; Subkey: "Software\SPHY_Model"; Flags: uninsdeletekey

[UninstallDelete]
Type: filesandordirs; Name: "{app}\env"
Type: filesandordirs; Name: "{app}\src"
Type: dirifempty; Name: "{app}"