import 'package:flutter/material.dart';
import 'package:ag_gimme_gist/core/app_router.dart';
import 'package:ag_gimme_gist/core/theme.dart';
import 'package:ag_gimme_gist/widgets/noise_background.dart';

void main() {
  runApp(const GimmeGistApp());
}

class GimmeGistApp extends StatelessWidget {
  const GimmeGistApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'GimmeGist',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      routerConfig: appRouter,
      builder: (context, child) {
        return NoiseBackground(
          child: child ?? const SizedBox.shrink(),
        );
      },
    );
  }
}
