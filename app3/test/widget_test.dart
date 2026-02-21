// WIDGET TEST
// Purpose: Verify app loads correctly and main screen renders.

import 'package:flutter_test/flutter_test.dart';
import 'package:eyecare/main.dart';

void main() {
  testWidgets('App loads successfully and shows login/register screens', (
    WidgetTester tester,
  ) async {
    // Load app
    await tester.pumpWidget(const MyApp());

    // Check if Login text is found
    expect(find.text('Login'), findsWidgets);
    expect(find.text('Register'), findsNothing);

    // Simulate tap on Login button if present
    // (Optional, based on your screen layout)
  });
}
