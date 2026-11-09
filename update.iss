#define MyAppName "SPHY_Model"
#define MyAppPublisher "Joris Eekhout/University of Murcia & CEBAS-CSIC"
#define MyAppExeName "launch.vbs"

[Setup]
; --- General Settings ---
; These MUST match the original installer so Windows knows it's an update
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName=C:\{#MyAppName}
PrivilegesRequired=admin

; Lock down the UI so the user clicks through instantly
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes

; --- Where the installer is built ---
SourceDir=G:\Otros ordenadores\Mi PC\data_analysis\python\sphy-gui\SPHY_Installer_Build\
Compression=lzma
SolidCompression=yes

[Files]
; ONLY package the code, GUI, and launchers. 
; Micromamba and the environment scripts are strictly excluded.
Source: "src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "launch.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "run_app.bat"; DestDir: "{app}"; Flags: ignoreversion

[Run]
; Launch the app directly instead of downloading the environment
Filename: "{app}\{#MyAppExeName}"; Description: "Launch SPHY Model"; Flags: shellexec postinstall nowait skipifsilent

[Registry]
; Keep the registry cleanup rule so the uninstaller stays fully functional
Root: HKCU; Subkey: "Software\SPHY_Model"; Flags: uninsdeletekey

[UninstallDelete]
; Keep the folder cleanup rules so the uninstaller knows what to delete
Type: filesandordirs; Name: "{app}\env"
Type: filesandordirs; Name: "{app}\src"
Type: dirifempty; Name: "{app}"