import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:multicast_dns/multicast_dns.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:webview_flutter/webview_flutter.dart';

const _multicastChannel = MethodChannel('ai.alpilab/multicast');
const _networkChannel = MethodChannel('ai.alpilab/network');

void main() => runApp(const AlpilabApp());

class AlpilabApp extends StatelessWidget {
  const AlpilabApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ALPILAB AI',
      theme: ThemeData.dark(useMaterial3: true),
      home: const HubFinderPage(),
    );
  }
}

class DiscoveredHub {
  DiscoveredHub({required this.name, required this.host, required this.port});
  final String name;
  final String host;
  final int port;
  String get url => 'http://$host:$port';
}

Future<String> _stableClientId(SharedPreferences prefs) async {
  final existing = prefs.getString('client_id');
  if (existing != null && existing.isNotEmpty) {
    return existing;
  }
  final id =
      'phone-${DateTime.now().millisecondsSinceEpoch.toRadixString(16)}';
  await prefs.setString('client_id', id);
  return id;
}

Future<String> _sessionFromHub(String hubUrl, {String fallback = 'repair-001'}) async {
  try {
    final res = await http.get(Uri.parse('$hubUrl/api/v1/hub/info'));
    if (res.statusCode < 400) {
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      final id = body['default_session_id'] as String?;
      if (id != null && id.trim().isNotEmpty) {
        return id.trim();
      }
    }
  } catch (_) {
    // fall through
  }
  return fallback;
}

class HubFinderPage extends StatefulWidget {
  const HubFinderPage({super.key});

  @override
  State<HubFinderPage> createState() => _HubFinderPageState();
}

enum _AuthProbe { authorized, unauthorized, offline }

class _HubFinderPageState extends State<HubFinderPage> {
  final List<DiscoveredHub> _hubs = [];
  String _status = 'Ricerca Local Hub…';
  bool _searching = false;

  @override
  void initState() {
    super.initState();
    _restoreThenSearch();
  }

  @override
  void dispose() {
    _multicastChannel.invokeMethod('release').catchError((_) {});
    super.dispose();
  }

  Future<void> _restoreThenSearch() async {
    final prefs = await SharedPreferences.getInstance();
    await _stableClientId(prefs);
    final hubUrl = prefs.getString('hub_url');
    final token = prefs.getString('pairing_token');
    final clientId = prefs.getString('client_id');
    final sessionId = prefs.getString('session_id');
    if (hubUrl != null &&
        token != null &&
        clientId != null &&
        sessionId != null &&
        mounted) {
      final ok = await _attemptAutoLogin(
        prefs: prefs,
        savedHubUrl: hubUrl,
        token: token,
        clientId: clientId,
        savedSessionId: sessionId,
      );
      if (ok) return;
    }
    await _search();
  }

  Future<bool> _attemptAutoLogin({
    required SharedPreferences prefs,
    required String savedHubUrl,
    required String token,
    required String clientId,
    required String savedSessionId,
  }) async {
    setState(() => _status = 'Connessione automatica…');
    // First try fresh discovery (mDNS + HTTP fallback), then fallback to saved hub.
    await _search();
    final savedUri = Uri.parse(savedHubUrl);
    final fallbackHub = DiscoveredHub(
      name: 'Alpilab Negozio',
      host: savedUri.host,
      port: savedUri.hasPort ? savedUri.port : 8000,
    );
    final targetHub = _hubs.isNotEmpty ? _hubs.first : fallbackHub;
    final liveSessionId = await _sessionFromHub(
      targetHub.url,
      fallback: savedSessionId,
    );
    final auth = await _probeSessionAuth(
      hub: targetHub,
      clientId: clientId,
      token: token,
      sessionId: liveSessionId,
    );
    if (auth == _AuthProbe.authorized) {
      await prefs.setString('hub_url', targetHub.url);
      await prefs.setString('session_id', liveSessionId);
      if (!mounted) return false;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => SessionPage(
            hub: targetHub,
            pairingToken: token,
            clientId: clientId,
            sessionId: liveSessionId,
          ),
        ),
      );
      return true;
    }
    if (auth == _AuthProbe.unauthorized) {
      await prefs.remove('pairing_token');
      await prefs.remove('session_id');
      if (!mounted) return false;
      setState(() {
        _status = 'Dispositivo non autorizzato — effettua nuovamente il pairing.';
      });
      return false;
    }
    return false;
  }

  Future<_AuthProbe> _probeSessionAuth({
    required DiscoveredHub hub,
    required String clientId,
    required String token,
    required String sessionId,
  }) async {
    final qp = Uri(
      scheme: 'ws',
      host: hub.host,
      port: hub.port,
      path: '/ws/sessions/$sessionId',
      queryParameters: {
        'device_id': clientId,
        'device_type': 'phone',
        'device_name': 'Android',
        'pairing_token': token,
      },
    );
    WebSocket? ws;
    try {
      ws = await WebSocket.connect(qp.toString()).timeout(const Duration(seconds: 4));
      ws.add(jsonEncode({'type': 'request_snapshot'}));
      final raw = await ws.first.timeout(const Duration(seconds: 4));
      final msg = jsonDecode(raw as String) as Map<String, dynamic>;
      if (msg['type'] == 'error') {
        final m = (msg['message'] as String?) ?? '';
        if (m == 'UNAUTHORIZED' || m == 'PAIRING_REQUIRED') {
          return _AuthProbe.unauthorized;
        }
        return _AuthProbe.offline;
      }
      if (msg['type'] == 'snapshot') {
        return _AuthProbe.authorized;
      }
    } catch (_) {
      return _AuthProbe.offline;
    } finally {
      await ws?.close();
    }
    return _AuthProbe.offline;
  }

  Future<void> _search() async {
    setState(() {
      _searching = true;
      _status = 'Ricerca Alpilab Negozio sulla LAN…';
      _hubs.clear();
    });

    // Phase 1: mDNS discovery
    debugPrint('ALPILAB: mDNS discovery started');
    final client = MDnsClient();
    try {
      try {
        await _multicastChannel.invokeMethod('acquire');
        debugPrint('ALPILAB: MulticastLock acquired');
      } catch (e) {
        debugPrint('ALPILAB: MulticastLock acquire failed: $e');
      }

      await client.start();
      final found = <String>{};
      final lookup = client.lookup<PtrResourceRecord>(
        ResourceRecordQuery.serverPointer('_alpilab._tcp.local'),
      );
      await for (final PtrResourceRecord ptr in lookup.timeout(
        const Duration(seconds: 6),
        onTimeout: (sink) => sink.close(),
      )) {
        await for (final SrvResourceRecord srv
            in client.lookup<SrvResourceRecord>(
          ResourceRecordQuery.service(ptr.domainName),
        )) {
          await for (final IPAddressResourceRecord ip
              in client.lookup<IPAddressResourceRecord>(
            ResourceRecordQuery.addressIPv4(srv.target),
          )) {
            final hub = DiscoveredHub(
              name: ptr.domainName.replaceAll('._alpilab._tcp.local', ''),
              host: ip.address.address,
              port: srv.port,
            );
            debugPrint('ALPILAB: mDNS discovered ${hub.name} at ${hub.url}');
            if (found.add(hub.url)) {
              setState(() => _hubs.add(hub));
            }
          }
        }
      }
    } on TimeoutException {
      // mDNS search window ended
    } catch (e, st) {
      debugPrint('ALPILAB: mDNS error: $e');
      debugPrint('ALPILAB: $st');
    } finally {
      client.stop();
      try {
        await _multicastChannel.invokeMethod('release');
        debugPrint('ALPILAB: MulticastLock released');
      } catch (e) {
        debugPrint('ALPILAB: MulticastLock release failed: $e');
      }
    }

    debugPrint('ALPILAB: mDNS found ${_hubs.length} hubs');

    // Phase 2: HTTP gateway fallback (only if mDNS found nothing)
    if (_hubs.isEmpty) {
      await _httpGatewayFallback();
    }

    setState(() {
      _searching = false;
      if (_hubs.isEmpty) {
        _status =
            'Nessun Hub trovato. Apri ALPILAB AI sul PC e resta sulla stessa Wi-Fi.';
      } else {
        _status = 'Seleziona Alpilab Negozio';
      }
    });
  }

  Future<void> _httpGatewayFallback() async {
    debugPrint('ALPILAB: mDNS found no hubs, trying HTTP gateway fallback');
    try {
      final String? gateway =
          await _networkChannel.invokeMethod<String>('getWifiGateway');
      if (gateway == null || gateway.isEmpty) {
        debugPrint('ALPILAB: HTTP gateway fallback failed (no gateway)');
        return;
      }
      debugPrint('ALPILAB: gateway detected: $gateway');

      final uri = Uri.parse('http://$gateway:8000/api/v1/hub/info');
      final httpClient = http.Client();
      try {
        final response = await httpClient
            .get(uri)
            .timeout(const Duration(seconds: 8));

        if (response.statusCode != 200) {
          debugPrint(
              'ALPILAB: HTTP gateway fallback failed (status ${response.statusCode})');
          return;
        }

        final body = jsonDecode(response.body) as Map<String, dynamic>;
        final name = body['name'] as String?;
        final sessionId = body['default_session_id'] as String?;
        if (name == null || sessionId == null) {
          debugPrint('ALPILAB: HTTP gateway fallback failed (invalid JSON)');
          return;
        }

        final hubHost = (body['lan_ip'] as String?) ?? gateway;
        const hubPort = 8000;
        final hub = DiscoveredHub(name: name, host: hubHost, port: hubPort);

        debugPrint('ALPILAB: HTTP gateway fallback succeeded: ${hub.url}');
        setState(() => _hubs.add(hub));
      } finally {
        httpClient.close();
      }
    } on TimeoutException {
      debugPrint('ALPILAB: HTTP gateway fallback failed (timeout)');
    } catch (e) {
      debugPrint('ALPILAB: HTTP gateway fallback failed ($e)');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ALPILAB AI')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(_status),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _searching ? null : _search,
              child: const Text('Cerca di nuovo'),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView(
                children: _hubs
                    .map(
                      (hub) => ListTile(
                        title: const Text('Alpilab Negozio'),
                        subtitle: Text(hub.url),
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => PairingPage(hub: hub),
                          ),
                        ),
                      ),
                    )
                    .toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class PairingPage extends StatefulWidget {
  const PairingPage({required this.hub, super.key});
  final DiscoveredHub hub;

  @override
  State<PairingPage> createState() => _PairingPageState();
}

class _PairingPageState extends State<PairingPage> {
  final _code = TextEditingController();
  String? _error;

  Future<void> _pair() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final clientId = await _stableClientId(prefs);
      final res = await http.post(
        Uri.parse('${widget.hub.url}/api/v1/pairing/complete'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'code': _code.text.trim(),
          'client_id': clientId,
          'client_type': 'phone',
          'platform': 'android',
          'device_name': 'Android',
        }),
      );
      if (res.statusCode >= 400) {
        setState(() => _error = 'Codice non valido o scaduto');
        return;
      }
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      final token = body['token'] as String?;
      if (token == null) {
        setState(() => _error = 'Pairing incompleto');
        return;
      }
      final sessionId = (body['session_id'] as String?)?.trim().isNotEmpty == true
          ? body['session_id'] as String
          : await _sessionFromHub(widget.hub.url);
      await prefs.setString('hub_url', widget.hub.url);
      await prefs.setString('pairing_token', token);
      await prefs.setString('client_id', body['client_id'] as String? ?? clientId);
      await prefs.setString('session_id', sessionId);
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => SessionPage(
            hub: widget.hub,
            pairingToken: token,
            clientId: body['client_id'] as String? ?? clientId,
            sessionId: sessionId,
          ),
        ),
      );
    } catch (e) {
      setState(() => _error = 'Hub non raggiungibile. Resta sulla stessa Wi-Fi del PC.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Pairing')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Text('Alpilab Negozio'),
            Text(widget.hub.url),
            const SizedBox(height: 12),
            const Text('Inserisci il codice a 6 cifre mostrato sul PC.'),
            TextField(
              controller: _code,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Codice'),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(_error!, style: const TextStyle(color: Colors.redAccent)),
              ),
            const SizedBox(height: 16),
            FilledButton(onPressed: _pair, child: const Text('Collega')),
          ],
        ),
      ),
    );
  }
}

class SessionPage extends StatefulWidget {
  const SessionPage({
    required this.hub,
    required this.pairingToken,
    required this.clientId,
    required this.sessionId,
    super.key,
  });
  final DiscoveredHub hub;
  final String pairingToken;
  final String clientId;
  final String sessionId;

  @override
  State<SessionPage> createState() => _SessionPageState();
}

class _SessionPageState extends State<SessionPage> {
  WebViewController? _controller;
  var _ready = false;

  @override
  void initState() {
    super.initState();
    _prepare();
  }

  Future<void> _prepare() async {
    final controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted);
    final origin = widget.hub.url;
    final identity = jsonEncode({
      'deviceId': widget.clientId,
      'pairingToken': widget.pairingToken,
      'sessionId': widget.sessionId,
      'deviceType': 'phone',
      'deviceName': 'Android',
    });
    await controller.loadRequest(Uri.parse('$origin/favicon.ico'));
    await Future<void>.delayed(const Duration(milliseconds: 120));
    await controller.runJavaScript('''
      (function() {
        const c = $identity;
        localStorage.setItem('alpilab.device_id', c.deviceId);
        localStorage.setItem('alpilab.pairing_token', c.pairingToken);
        localStorage.setItem('alpilab.session_id', c.sessionId);
        localStorage.setItem('alpilab.device_type', c.deviceType);
        localStorage.setItem('alpilab.device_name', c.deviceName);
      })();
    ''');
    await controller.loadRequest(Uri.parse('$origin/'));
    if (!mounted) return;
    setState(() {
      _controller = controller;
      _ready = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('RepairSession')),
      body: _ready && _controller != null
          ? WebViewWidget(controller: _controller!)
          : const Center(child: CircularProgressIndicator()),
    );
  }
}
