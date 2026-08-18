# V0.5.1 — Installable local clients

Packaging and device validation on top of V0.5. No new product features.

## Windows EXE

```powershell
.\scripts\build_windows_exe.ps1
```

Output: `dist\ALPILAB AI.exe`

User data (editable without rebuild):

```text
%USERPROFILE%\.alpilab\
  config.json
  windows_apps.json
  logs\
  data\alpilab.db
  storage\
```

The EXE starts Local Hub + embedded WebView + PC Agent (`--agent` child process). It does **not** open Chrome.

Future (not V0.5.1): MSI installer, Start with Windows, tray, Windows Service.

## 3uTools

Search order: env `ALPILAB_WINAPP_3UTOOLS_PATH` → `windows_apps.json` → known Program Files locations of **3uTools.exe only**.

## Android APK

Flutter SDK is **not** in the cloud agent environment. On a Windows/macOS machine with Flutter:

```powershell
.\scripts\prepare_android_client.ps1
cd clients\alpilab_mobile
flutter build apk --debug
```

Merge `android_overlay/AndroidManifest.xml` (cleartext HTTP + multicast) into the generated AndroidManifest.

## Client WebSocket auth

| Endpoint | Auth |
|----------|------|
| `/ws/agent/{session}` | Unchanged V0.4 (PC Agent) |
| `/ws/sessions/{session}` | Pairing token required when SQLite hub is on, except loopback `device_type=pc` |

Revoked devices lose access. Tokens are not written to logs.

## Photo storage

`POST /api/v1/sessions/{id}/photos` stores files under `~/.alpilab/storage/{session}/photos/`. No editor.

## Cost

Zero required cloud. LAN + PC + devices only.
