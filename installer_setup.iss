; Android Multi-Tool Pro — Windows Setup (Inno Setup 6)
; Clean, neat installer like Oumse GSM — installs to Program Files, creates shortcuts, registers uninstall
; Build: double-click build_installer.bat or run "iscc installer_setup.iss" (Inno Setup 6 required)

#define MyAppName "Android Multi-Tool Pro"
#define MyAppVersion "2.5.0"
#define MyAppPublisher "GSM Technician Solutions"
#define MyAppURL "https://github.com/android-multi-tool"
#define MyAppExeName "AndroidMultiTool.exe"

[Setup]
AppId={{D8A13B4E-4B02-4C67-8C53-8A2F2295E7C1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\AndroidMultiToolPro
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=README.md
OutputDir=dist\installer
OutputBaseFilename=AndroidMultiTool_Setup_v2.5
SetupIconFile=bin\adb.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64
MinVersion=6.1sp1
UninstallDisplayName={#MyAppName} {#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup — 100% Offline, no credits
VersionInfoCopyright=2026 {#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
DisableProgramGroupPage=yes
ShowLanguageDialog=no
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
OutputManifestFile=installer_manifest.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "installdrivers"; Description: "Install MediaTek + Transsion USB drivers (VID 0x0E8D / 0x2E04)"; GroupDescription: "Drivers:"

[Files]
; Main executable (PyInstaller bundle)
Source: "dist\AndroidMultiTool.exe"; DestDir: "{app}"; Flags: ignoreversion
; Bundled ADB / Fastboot + drivers
Source: "bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
; Driver helpers
Source: "install_drivers.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "bin\drivers\*"; DestDir: "{app}\bin\drivers"; Flags: ignoreversion recursesubdirs createallsubdirs
; Docs
Source: "README.md"; DestDir: "{app}"; Flags: isreadme ignoreversion
Source: "web\*"; DestDir: "{app}\web"; Flags: ignoreversion recursesubdirs createallsubdirs
; Keep installer artifacts for debugging
Source: "installer_setup.iss"; DestDir: "{app}"; Flags: ignoreversion
Source: "build_installer.bat"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Comment: "Launch {#MyAppName} — Offline Tecno/Infinix/Itel toolkit"
Name: "{group}\Install Drivers (Transsion + MediaTek)"; Filename: "{app}\install_drivers.bat"; WorkingDir: "{app}"; Comment: "Install USB drivers for MTK BROM/Preloader detection"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; Comment: "Uninstall {#MyAppName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppName} v{#MyAppVersion} — 100% Offline"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppName} v{#MyAppVersion}"

[Registry]
; Register install location for detection by the app itself
Root: HKLM; Subkey: "SOFTWARE\AndroidMultiToolPro"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\AndroidMultiToolPro"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey
; ADB Vendor IDs like Oumse — ensure Transsion & MediaTek are recognized
Root: HKCU; Subkey: "Software\AndroidMultiToolPro"; ValueType: dword; ValueName: "Installed"; ValueData: "1"; Flags: uninsdeletekey

[Run]
Filename: "{app}\install_drivers.bat"; Description: "Install USB drivers now (recommended)"; Flags: postinstall skipifsilent runascurrentuser unchecked; Tasks: installdrivers
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\__pycache__"
