import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:ag_gimme_gist/models/appointment.dart';
import 'package:ag_gimme_gist/services/health_connect_service.dart';

class IngestViewModel extends ChangeNotifier {
  final HealthConnectService _healthService = HealthConnectService();

  bool _isSyncingHealth = false;
  bool get isSyncingHealth => _isSyncingHealth;

  bool _isUploading = false;
  bool get isUploading => _isUploading;

  List<HealthDataPoint> _recentData = [];
  List<HealthDataPoint> get recentData => _recentData;

  Map<String, HealthDataPoint> get latestDataByType {
    final Map<String, HealthDataPoint> map = {};
    for (var point in _recentData) {
      if (!map.containsKey(point.dataType) || point.timestamp.isAfter(map[point.dataType]!.timestamp)) {
        map[point.dataType] = point;
      }
    }
    return map;
  }

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  List<PlatformFile> _uploadedFiles = [];
  List<PlatformFile> get uploadedFiles => _uploadedFiles;

  void initialize(Appointment appointment) {
    bool hasData = false;
    if (appointment.ingestedHealthData != null) {
      hasData = true;
      _recentData = appointment.ingestedHealthData!.map((metric) => HealthDataPoint(
            dataType: metric.type,
            value: metric.value,
            unit: metric.unit,
            timestamp: DateTime.parse(metric.timestamp),
          )).toList();
    }
    if (appointment.uploadedFiles != null) {
      hasData = true;
      _uploadedFiles = appointment.uploadedFiles!.map((file) => PlatformFile(
            name: file.name,
            size: file.size,
          )).toList();
    }
    
    if (hasData) notifyListeners();
  }

  Future<void> syncWearableData({
    required bool isMocked,
    required DateTime start,
    required DateTime end,
  }) async {
    _isSyncingHealth = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final hasPermissions = isMocked ? true : await _healthService.authorize();
      if (hasPermissions) {
        _recentData = await _healthService.fetchRecentData(
          isMocked: isMocked,
          startTime: start,
          endTime: end,
        );
      } else {
        _errorMessage = 'Permission denied to access Health Connect.';
      }
    } catch (e) {
      _errorMessage = 'Failed to sync: \$e';
    } finally {
      _isSyncingHealth = false;
      notifyListeners();
    }
  }

  Future<void> uploadDiagnosticReport() async {
    _isUploading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'jpg', 'png', 'jpeg'],
        allowMultiple: true,
      );

      if (result != null) {
        _uploadedFiles.addAll(result.files);
        // Here you would typically upload the file to Firebase Storage
        // For now, we simulate an upload processing time
        await Future.delayed(const Duration(seconds: 2));
      }
    } catch (e) {
      _errorMessage = 'Failed to pick file: \$e';
    } finally {
      _isUploading = false;
      notifyListeners();
    }
  }
}
