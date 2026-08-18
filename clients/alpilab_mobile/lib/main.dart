import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:multicast_dns/multicast_dns.dart';
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
    _search();
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
      await for (final PtrResourceRecord ptr in client.lookup<PtrResourceRecord>(
        ResourceRecordQuery.serverPointer('_alpilab._tcp.local'),
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
            if (!_hubs.any((h) => h.url == hub.url)) {
              setState(() => _hubs.add(hub));
            }
          }
        }
      }
    } catch (e) {
      setState(() => _status = 'Discovery non disponibile: $e');
    } finally {
      client.stop();
      setState(() {
        _searching = false;
        if (_hubs.isEmpty && !_status.startsWith('Discovery')) {
          _status = 'Nessun Hub trovato. Verifica Wi-Fi e Local Hub.';
        } else if (_hubs.isNotEmpty) {
          _status = 'Seleziona un Hub';
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
                        title: Text(hub.name.isEmpty ? 'Alpilab Negozio' : hub.name),
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
      final res = await http.post(
        Uri.parse('${widget.hub.url}/api/v1/pairing/complete'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'code': _code.text.trim(),
          'client_type': 'phone',
          'platform': 'android',
          'device_name': 'Android',
        }),
      );
      if (res.statusCode >= 400) {
        setState(() => _error = 'Codice non valido');
        return;
      }
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => SessionPage(hub: widget.hub)),
      );
    } catch (e) {
      setState(() => _error = 'Connessione Hub fallita');
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
            Text('Hub: ${widget.hub.url}'),
            const SizedBox(height: 12),
            const Text('Inserisci il codice mostrato sul PC (Collega dispositivo).'),
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
  const SessionPage({required this.hub, super.key});
  final DiscoveredHub hub;

  @override
  State<SessionPage> createState() => _SessionPageState();
}

class _SessionPageState extends State<SessionPage> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadRequest(Uri.parse('${widget.hub.url}/'));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('RepairSession')),
      body: WebViewWidget(controller: _controller),
    );
  }
}
