# Alpilab Mobile (Flutter) — V0.5.1

## Flutter in questo ambiente

Il cloud agent **non ha Flutter SDK**. La build APK **non è stata eseguita qui**.

Sul PC:

```powershell
flutter --version
flutter doctor
.\scripts\prepare_android_client.ps1
cd clients\alpilab_mobile
flutter build apk --debug
```

APK: `build/app/outputs/flutter-apk/app-debug.apk` (installazione manuale, nessun Play Store).

Copia i permessi da `android_overlay/AndroidManifest.xml` (Internet, multicast, **cleartext HTTP** LAN).

## Flusso

1. Local Hub sul PC (ALPILAB AI.exe)
2. App cerca **Alpilab Negozio** (mDNS, timeout ~6s)
3. Codice pairing 6 cifre
4. Token e `device_id` salvati in SharedPreferences (stabile tra riavvii)
5. RepairSession dal Local Hub (`/api/v1/hub/info`), iniettata in localStorage — niente `?session=` / token in pagina

iOS: stesso Dart, build solo su macOS.
