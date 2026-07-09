import 'package:flutter_test/flutter_test.dart';

import 'package:richy_lite/main.dart';

void main() {
  testWidgets('App launches smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const RichyApp());
    // Verify the app renders without crashing
    expect(find.text('RICHY'), findsOneWidget);
  });
}
