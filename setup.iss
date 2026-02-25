[Setup]
; App Information
AppName=SpeedMonitor
AppVersion=1.0.0
AppPublisher=Mamun Abdullah (memamun)
AppPublisherURL=https://github.com/memamun/internet-speed-monitor
AppSupportURL=https://github.com/memamun/internet-speed-monitor/issues
AppUpdatesURL=https://github.com/memamun/internet-speed-monitor/releases

; Installer settings
DefaultDirName={autopf}\SpeedMonitor
DefaultGroupName=SpeedMonitor
AllowNoIcons=yes
OutputDir=build_installer
OutputBaseFilename=SpeedMonitor_Setup_v1.0.0
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

; Privilege requirements
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
RestartApplications=yes
AppMutex=SpeedMonitorMutex

; Wizard styling
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Launch SpeedMonitor automatically when Windows starts"; GroupDescription: "Auto-start:"

[Files]
; Main executable
Source: "dist\SpeedMonitor.exe"; DestDir: "{app}"; Flags: ignoreversion

; Assets folder (if needed at runtime, though PyInstaller bundled it; good to have)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcuts
Name: "{group}\SpeedMonitor"; Filename: "{app}\SpeedMonitor.exe"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\{cm:UninstallProgram,SpeedMonitor}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\SpeedMonitor"; Filename: "{app}\SpeedMonitor.exe"; Tasks: desktopicon; IconFilename: "{app}\assets\icon.ico"

; Startup shortcut
Name: "{userstartup}\SpeedMonitor"; Filename: "{app}\SpeedMonitor.exe"; Tasks: startup; IconFilename: "{app}\assets\icon.ico"

[Run]
; Run after install
Filename: "{app}\SpeedMonitor.exe"; Description: "{cm:LaunchProgram,SpeedMonitor}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /F /IM SpeedMonitor.exe /T"; RunOnceId: "KillProcess"; Flags: runhidden
