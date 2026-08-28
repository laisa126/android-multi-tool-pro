; Script generated for Inno Setup 6
; Compiles Android Multi-Tool Pro Setup (.exe installer)

#define MyAppName "Android Multi-Tool Pro"
#define MyAppVersion "2.5.0"
#define MyAppPublisher "GSM Technician Solutions"
#define MyAppExeName "AndroidMultiTool.exe"

[Setup]
AppId={{D8A13B4E-4B02-4C67-8C53-8A2F2295E7C1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\AndroidMultiToolPro
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=AndroidMultiTool_Setup_v2.5
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\AndroidMultiTool.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "install_drivers.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Install Drivers"; Filename: "{app}\install_drivers.bat"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
