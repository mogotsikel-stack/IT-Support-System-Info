; ==========================================================
; IT Connect Installer Script
; Publisher: Service Desk DevOps
; Auto-start for all users (FORCED)
; Requires Admin Rights
; ==========================================================

[Setup]
AppName=IT Connect
AppVersion=1.0
AppPublisher=Service Desk DevOps
DefaultDirName={autopf}\IT Connect
DefaultGroupName=IT Connect
UninstallDisplayIcon={app}\it_connect.exe
OutputDir=Output
OutputBaseFilename=IT_Connect_Setup
SetupIconFile=logo.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern

[Files]
Source: "dist\it_connect.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\IT Connect"; Filename: "{app}\it_connect.exe"
Name: "{userdesktop}\IT Connect"; Filename: "{app}\it_connect.exe"

[Registry]
; ==========================================================
; FORCED AUTO-START FOR ALL USERS
; Writes to the REAL startup location:
; HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
; ==========================================================
Root: HKLM64; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "IT Connect"; \
    ValueData: """{app}\it_connect.exe"""; Flags: uninsdeletevalue

[Run]
Filename: "{app}\it_connect.exe"; Description: "Launch IT Connect"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\it_connect.exe"
Type: files; Name: "{app}\logo.ico"
