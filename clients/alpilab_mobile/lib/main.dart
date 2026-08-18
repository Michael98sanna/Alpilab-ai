import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:multicast_dns/multicast_dns.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:webview_flutter/webview_flutter.dart';

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

class HubFinderPage extends StatefulWidget {
  const HubFinderPage({super.key});

  @override
  State<HubFinderPage> createState() => _HubFinderPageState();
}

class _HubFinderPageState extends State<HubFinderPage> {
  final List<DiscoveredHub> _hubs = [];
  String _status = 'Ricerca Local Hub…';
  bool _searching = false;

  @override
  void initState() {
    super.initState();
    _restoreThenSearch();
  }

  Future<void> _restoreThenSearch() async {
    final prefs = await SharedPreferences.getInstance();
    final hubUrl = prefs.getString('hub_url');
    final token = prefs.getString('pairing_token');
    final clientId = prefs.getString('client_id');
    if (hubUrl != null && token != null && clientId != null && mounted) {
      final uri = Uri.parse(hubUrl);
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => SessionPage(
            hub: DiscoveredHub(
              name: 'Alpilab Negozio',
              host: uri.host,
              port: uri.hasPort ? uri.port : 8000,
            ),
            pairingToken: token,
            clientId: clientId,
          ),
        ),
      );
      return;
    }
    await _search();
  }

  Future<void> _search() async {
    setState(() {
      _searching = true;
      _status = 'Ricerca Alpilab Negozio sulla LAN…';
      _hubs.clear();
    });
    final client = MDnsClient();
    try {
      await client.start();
      final found = <String>{};
      final lookup = client.lookup<PtrResourceRecord>(
        ResourceRecordQuery.serverPointer('_alpilab._tcp.local'),
      );
      await for (final PtrResourceRecord ptr in lookup.timeout(
        const Duration(seconds: 6),
        onTimeout: (sink) => sink.close(),
      )) {
        await for (final SrvResourceRecord srv in client.lookup<SrvResourceRecord>(
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
            if (found.add(hub.url)) {
              setState(() => _hubs.add(hub));
            }
          }
        }
      }
    } on TimeoutException {
      // search window ended
    } catch (e) {
      setState(() => _status = 'Discovery non disponibile. Verifica Wi-Fi e Local Hub.');
    } finally {
      client.stop();
      setState(() {
        _searching = false;
        if (_hubs.isEmpty && !_status.startsWith('Discovery')) {
          _status =
              'Nessun Hub trovato. Apri ALPILAB AI sul PC e resta sulla stessa Wi-Fi.';
        } else if (_hubs.isNotEmpty) {
          _status = 'Seleziona Alpilab Negozio';
        }
      });
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
      final clientId = prefs.getString('client_id') ??
          'phone-${DateTime.now().millisecondsSinceEpoch}';
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
      await prefs.setString('hub_url', widget.hub.url);
      await prefs.setString('pairing_token', token);
      await prefs.setString('client_id', body['client_id'] as String? ?? clientId);
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => SessionPage(
            hub: widget.hub,
            pairingToken: token,
            clientId: body['client_id'] as String? ?? clientId,
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
    super.key,
  });
  final DiscoveredHub hub;
  final String pairingToken;
  final String clientId;

  @override
  State<SessionPage> createState() => _SessionPageState();
}

class _SessionPageState extends State<SessionPage> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    final uri = Uri.parse(widget.hub.url).replace(queryParameters: {
      'pairing_token': widget.pairingToken,
      'device_id': widget.clientId,
      'device_type': 'phone',
      'device_name': 'Android',
      'session': 'repair-001',
    });
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadRequest(uri);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('RepairSession')),
      body: WebViewWidget(controller: _controller),
    );
  }
}
