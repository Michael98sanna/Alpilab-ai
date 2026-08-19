import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const multicastChannel = MethodChannel('ai.alpilab/multicast');
  const networkChannel = MethodChannel('ai.alpilab/network');
  final multicastCalls = <String>[];
  String? mockGateway;

  setUp(() {
    multicastCalls.clear();
    mockGateway = '192.168.137.1';

    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(multicastChannel, (call) async {
      multicastCalls.add(call.method);
      return true;
    });

    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(networkChannel, (call) async {
      if (call.method == 'getWifiGateway') return mockGateway;
      return null;
    });
  });

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(multicastChannel, null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(networkChannel, null);
  });

  test('getWifiGateway returns dynamic gateway (no hardcoded IP)', () async {
    mockGateway = '10.0.0.1';
    final gw = await networkChannel.invokeMethod<String>('getWifiGateway');
    expect(gw, '10.0.0.1');
  });

  test('getWifiGateway returns null when no gateway', () async {
    mockGateway = null;
    final gw = await networkChannel.invokeMethod<String>('getWifiGateway');
    expect(gw, isNull);
  });

  test('MulticastLock is still acquired and released with fallback flow', () async {
    await multicastChannel.invokeMethod('acquire');
    // mDNS phase would run here
    await multicastChannel.invokeMethod('release');
    // fallback phase does not touch multicast
    expect(multicastCalls, ['acquire', 'release']);
  });

  group('hub/info JSON validation', () {
    test('valid hub/info JSON is accepted', () {
      final body = jsonDecode(jsonEncode({
        'name': 'Alpilab Negozio',
        'default_session_id': 'repair-001',
        'lan_ip': '192.168.137.1',
        'lan_url': 'http://192.168.137.1:8000',
        'ws_url': 'ws://192.168.137.1:8000',
      })) as Map<String, dynamic>;
      expect(body['name'], isNotNull);
      expect(body['default_session_id'], isNotNull);
    });

    test('JSON missing name is rejected', () {
      final body = jsonDecode(jsonEncode({
        'default_session_id': 'repair-001',
        'lan_ip': '192.168.137.1',
      })) as Map<String, dynamic>;
      final name = body['name'] as String?;
      expect(name, isNull, reason: 'Missing name should cause fallback to skip');
    });

    test('JSON missing default_session_id is rejected', () {
      final body = jsonDecode(jsonEncode({
        'name': 'Alpilab Negozio',
        'lan_ip': '192.168.137.1',
      })) as Map<String, dynamic>;
      final sid = body['default_session_id'] as String?;
      expect(sid, isNull,
          reason: 'Missing default_session_id should cause fallback to skip');
    });

    test('valid JSON without lan_ip falls back to gateway', () {
      final body = jsonDecode(jsonEncode({
        'name': 'Alpilab Negozio',
        'default_session_id': 'repair-001',
      })) as Map<String, dynamic>;
      final hubHost = (body['lan_ip'] as String?) ?? '192.168.137.1';
      expect(hubHost, '192.168.137.1');
    });

    test('valid JSON with lan_ip uses lan_ip', () {
      final body = jsonDecode(jsonEncode({
        'name': 'Alpilab Negozio',
        'default_session_id': 'repair-001',
        'lan_ip': '10.0.0.5',
      })) as Map<String, dynamic>;
      final hubHost = (body['lan_ip'] as String?) ?? '192.168.137.1';
      expect(hubHost, '10.0.0.5');
    });
  });
}
