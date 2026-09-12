#define AppName "CAISSA-JEPA"
#define AppVersion "7.1"
#define AppPublisher "CAISSA-JEPA Research"
#ifndef AppBuildDir
  #define AppBuildDir "..\dist\Caissa-JEPA"
#endif

[Setup]
AppId={{B78ABBD9-FE4A-4F8A-9DF0-CAISSAJEPA0001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\CAISSA-JEPA
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\installer-output
OutputBaseFilename=CAISSA-JEPA-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName}

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "{#AppBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\Caissa-JEPA.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\Caissa-JEPA.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Caissa-JEPA.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
