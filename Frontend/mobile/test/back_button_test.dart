import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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
  testWidgets('Test back button on all screens', (WidgetTester tester) async {
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

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    final router = ProviderScope.containerOf(tester.element(find.byType(UrbanSenseApp))).read(routerProvider);

    final testRoutes = ['/profile', '/incidents', '/map', '/monitor', '/camera'];

    for (final route in testRoutes) {
      print('\n=========================================');
      print('TESTING ROUTE: $route (via context.go)');
      print('=========================================');
      router.go(route);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      final backFinder = find.byIcon(Icons.arrow_back_ios_rounded);
      if (backFinder.evaluate().isNotEmpty) {
        print('Tapping AppBar back button on $route...');
        await tester.tap(backFinder.first);
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));
        print('Finished tapping back button on $route');
      }
    }
  });
}
