# Alpilab Mobile (Flutter)

Client Android / iOS / tablet per il **Local Hub**.

## Stato V0.5

Flutter **non è installato** nell'ambiente di sviluppo cloud. Il codice client è nel repo; la compilazione APK va fatta sul PC con Flutter SDK.

```bash
# https://docs.flutter.dev/get-started/install
flutter create --platforms=android,ios,windows .
flutter pub get
flutter run -d android
```

Da eseguire nella cartella `clients/alpilab_mobile` dopo `flutter create` per generare le cartelle `android/` e `ios/` (non versionate qui per evitare una toolchain enorme).

Flusso:

1. Avvia Local Hub sul PC
2. Apri l'app → cerca `_alpilab._tcp`
3. Seleziona **Alpilab Negozio**
4. Inserisci il codice pairing del PC
5. Entra in RepairSession (WebView verso il Hub)

iOS è pronto a livello di codice Dart; la build iOS richiede macOS/Xcode.

Tablet Android usa lo stesso APK.
