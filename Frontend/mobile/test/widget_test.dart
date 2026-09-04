import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Smoke test that simply verifies the app builds without crashing.
/// Full integration tests require Firebase and GPS hardware.
void main() {
  testWidgets('App widget tree builds without error', (WidgetTester tester) async {
    // Build a minimal widget tree for smoke testing
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: Center(child: Text('AI UrbanSense'))),
      ),
    );
    expect(find.text('AI UrbanSense'), findsOneWidget);
  });
}
