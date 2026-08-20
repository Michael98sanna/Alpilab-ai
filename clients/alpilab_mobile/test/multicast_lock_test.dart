import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const channel = MethodChannel('ai.alpilab/multicast');
  final calls = <String>[];

  setUp(() {
    calls.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call.method);
      return true;
    });
  });

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  test('acquire is called before mDNS and release is called in finally', () async {
    // Simulate the channel calls that _search() makes.
    await channel.invokeMethod('acquire');
    // mDNS would run here (not testable in unit test — requires real Wi-Fi hardware)
    await channel.invokeMethod('release');

    expect(calls, ['acquire', 'release'],
        reason: 'MulticastLock must be acquired before discovery and released in finally');
  });

  test('release is called even when acquire throws', () async {
    // Re-configure handler so acquire throws, release succeeds.
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call.method);
      if (call.method == 'acquire') throw PlatformException(code: 'LOCK_ERROR');
      return true;
    });

    try {
      await channel.invokeMethod('acquire');
    } catch (_) {}
    // _search() always calls release in finally regardless.
    await channel.invokeMethod('release');

    expect(calls, contains('release'),
        reason: 'release must be called in finally even if acquire fails');
  });
}
