; Inno Setup installer for the unsigned Windows one-directory bundle
; (ARCHITECTURE_V1.md §6.2). Signing is a maintainer decision.
#define MyAppName "RoomScope"
#define MyAppVersion "0.1.0.dev1"
#define MyAppPublisher "RoomScope contributors"
#define MyAppURL "https://github.com/jingyemingyue/RoomScope"
#define MyAppExeName "roomscope.exe"

[Setup]
AppId={{8E0C2B3A-6F41-4C7D-9A11-7C2E1A0B4D5F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
OutputBaseFilename=RoomScope-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
LicenseFile=..\..\LICENSE
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\..\dist\roomscope\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch RoomScope"; Flags: nowait postinstall skipifsilent
