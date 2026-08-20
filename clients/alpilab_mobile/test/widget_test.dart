import 'package:flutter_test/flutter_test.dart';
import 'package:alpilab_mobile/main.dart';

void main() {
  testWidgets('ALPILAB AI app loads', (WidgetTester tester) async {
    await tester.pumpWidget(const AlpilabApp());
    await tester.pump();
    expect(find.text('ALPILAB AI'), findsWidgets);
  });
}
