import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:urbansense_mobile/app/app.dart';
import 'package:urbansense_mobile/app/router.dart';
import 'package:urbansense_mobile/core/storage/secure_storage.dart';

class MockSecureStorage extends SecureStorageService {
  @override
  Future<bool> isAuthenticated() async => true;
  @override
  Future<String?> getUserId() async => 'test-user-id';
  @override
  Future<String?> getRole() async => 'DRIVER';
}

void main() {
  setUp(() {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  testWidgets('Root screen (/dashboard) system back button does not crash', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() => tester.view.resetPhysicalSize());

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          secureStorageProvider.overrideWithValue(MockSecureStorage()),
        ],
        child: const UrbanSenseApp(),
      ),
    );

    await tester.pumpAndSettle();
    expect(find.text("Today's Detections"), findsOneWidget);

    // System back on root screen
    final handled = await tester.binding.handlePopRoute();
    expect(handled, isFalse); // Root route gives OS control to minimize, no crash
    await tester.pump();
    expect(find.text("Today's Detections"), findsOneWidget);
  });

  testWidgets('Bottom navigation pushes screens and back button returns to dashboard', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() => tester.view.resetPhysicalSize());

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          secureStorageProvider.overrideWithValue(MockSecureStorage()),
        ],
        child: const UrbanSenseApp(),
      ),
    );

    await tester.pumpAndSettle();

    // 1. Test Profile
    await tester.tap(find.text('Profile'));
    await tester.pumpAndSettle();
    expect(find.text('Driver Profile'), findsOneWidget);

    // Tap AppBar back button
    await tester.tap(find.byIcon(Icons.arrow_back_ios_rounded));
    await tester.pumpAndSettle();
    expect(find.text("Today's Detections"), findsOneWidget);

    // 2. Test Incidents
    await tester.tap(find.descendant(of: find.byType(BottomNavigationBar), matching: find.text('Incidents')));
    await tester.pumpAndSettle();
    expect(find.text('Incidents & Alerts'), findsOneWidget);

    // System back button
    final handledIncidents = await tester.binding.handlePopRoute();
    expect(handledIncidents, isTrue);
    await tester.pumpAndSettle();
    expect(find.text("Today's Detections"), findsOneWidget);

    // 3. Test Map
    await tester.tap(find.text('Map'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('Live GIS Map & Hazards'), findsOneWidget);

    // Tap AppBar back button
    await tester.tap(find.byIcon(Icons.arrow_back_ios_rounded));
    await tester.pumpAndSettle();
    expect(find.text("Today's Detections"), findsOneWidget);

    // 4. Test Monitoring
    await tester.tap(find.text('START MONITORING'));
    await tester.pumpAndSettle();
    expect(find.text('AI MONITORING ACTIVE'), findsOneWidget);

    // Open Camera from monitoring
    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();
    expect(find.text('LIVE AI'), findsOneWidget);

    // Tap back button on camera
    await tester.tap(find.byIcon(Icons.arrow_back_ios_rounded));
    await tester.pumpAndSettle();
    expect(find.text('AI MONITORING ACTIVE'), findsOneWidget);

    // Stop monitoring returns to dashboard
    await tester.tap(find.text('STOP MONITORING'));
    await tester.pumpAndSettle();
    expect(find.text("Today's Detections"), findsOneWidget);
  });

  testWidgets('Directly opened child screen does not crash on back button and returns to dashboard', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() => tester.view.resetPhysicalSize());

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          secureStorageProvider.overrideWithValue(MockSecureStorage()),
        ],
        child: const UrbanSenseApp(),
      ),
    );

    await tester.pumpAndSettle();
    final router = ProviderScope.containerOf(tester.element(find.byType(UrbanSenseApp))).read(routerProvider);

    // Directly go to /profile without history
    router.go('/profile');
    await tester.pumpAndSettle();
    expect(find.text('Driver Profile'), findsOneWidget);

    // Tap AppBar back button - should safely go to /dashboard instead of crashing
    await tester.tap(find.byIcon(Icons.arrow_back_ios_rounded));
    await tester.pumpAndSettle();
    expect(find.text("Today's Detections"), findsOneWidget);

    // Directly go to /incidents without history
    router.go('/incidents');
    await tester.pumpAndSettle();
    expect(find.text('Incidents & Alerts'), findsOneWidget);

    // Tap AppBar back button - should safely go to /dashboard instead of crashing
    await tester.tap(find.byIcon(Icons.arrow_back_ios_rounded));
    await tester.pumpAndSettle();
    expect(find.text("Today's Detections"), findsOneWidget);
  });
}
