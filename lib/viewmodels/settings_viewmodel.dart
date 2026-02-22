import 'package:flutter/material.dart';

enum AppMode { real, mocked }

class SettingsViewModel extends ChangeNotifier {
  AppMode _currentMode = AppMode.mocked; // Default to mocked per user request

  AppMode get currentMode => _currentMode;

  bool get isMocked => _currentMode == AppMode.mocked;

  void toggleMode(AppMode mode) {
    if (_currentMode != mode) {
      _currentMode = mode;
      notifyListeners();
    }
  }
}
