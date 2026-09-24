; Inno Setup installer for the unsigned Windows one-directory bundle
; (ARCHITECTURE_V1.md §6.2). Signing is a maintainer decision.
;
; Build from the repository root after PyInstaller has produced dist\roomscope:
;   iscc /DMyAppVersion=<pyproject version> packaging\windows\roomscope.iss
; The installer is written to dist\RoomScope-setup.exe.
#define MyAppName "RoomScope"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0.dev0"
#endif
#define MyAppPublisher "RoomScope contributors"
#define MyAppURL "https://github.com/jingyemingyue/RoomScope"
; Windowed launcher: opens the GUI without a console window. The console
; roomscope.exe next to it is the CLI.
#define MyAppExeName "roomscope-gui.exe"

[Setup]
AppId={{8E0C2B3A-6F41-4C7D-9A11-7C2E1A0B4D5F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\..\dist
OutputBaseFilename=RoomScope-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=..\..\LICENSE
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Replace the whole previous version so no stale library survives an upgrade.
Source: "..\..\dist\roomscope\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Third-party licenses"; Filename: "{app}\THIRD_PARTY_LICENSES"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
