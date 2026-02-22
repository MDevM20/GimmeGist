import 'package:health/health.dart';
import 'package:flutter/foundation.dart';
import 'dart:io';

class HealthDataPoint {
  final String dataType;
  final double value;
  final String unit;
  final DateTime timestamp;

  HealthDataPoint({
    required this.dataType,
    required this.value,
    required this.unit,
    required this.timestamp,
  });
}

class HealthConnectService {
  final Health _health = Health();

  static const List<HealthDataType> allTypes = [
    HealthDataType.ACTIVE_ENERGY_BURNED,
    HealthDataType.BASAL_ENERGY_BURNED,
    HealthDataType.BLOOD_GLUCOSE,
    HealthDataType.BLOOD_OXYGEN,
    HealthDataType.BLOOD_PRESSURE_DIASTOLIC,
    HealthDataType.BLOOD_PRESSURE_SYSTOLIC,
    HealthDataType.BODY_FAT_PERCENTAGE,
    HealthDataType.BODY_TEMPERATURE,
    HealthDataType.HEART_RATE,
    HealthDataType.HEART_RATE_VARIABILITY_RMSSD,
    HealthDataType.HEIGHT,
    HealthDataType.RESTING_HEART_RATE,
    HealthDataType.STEPS,
    HealthDataType.WEIGHT,
    HealthDataType.SLEEP_ASLEEP,
  ];

  Future<bool> authorize() async {
    await _health.configure();
    final permissions = allTypes.map((e) => HealthDataAccess.READ).toList();

    try {
      if (Platform.isAndroid) {
        debugPrint('Checking Health Connect Status...');
        var status = _health.healthConnectSdkStatus;
        debugPrint('Health Connect SDK Status currently explicitly accessed: $status');
        bool isAvailable = await _health.isHealthConnectAvailable();
        debugPrint('Is Health Connect Available? $isAvailable');
      }

      debugPrint('Requesting authorization for \$allTypes');
      bool success = await _health.requestAuthorization(allTypes, permissions: permissions);
      debugPrint('Authorization success: \$success');
      return success;
    } catch (e) {
      debugPrint('Health Auth Error: \$e');
      rethrow;
    }
  }

  Future<List<HealthDataPoint>> fetchRecentData({
    required bool isMocked,
    required DateTime startTime,
    required DateTime endTime,
  }) async {
    if (isMocked) {
      // Return mocked data to simulate physiological anomalies within the range
      await Future.delayed(const Duration(seconds: 1));
      return [
        HealthDataPoint(dataType: 'Heart Rate', value: 72, unit: 'bpm', timestamp: endTime.subtract(const Duration(hours: 2))),
        HealthDataPoint(dataType: 'Heart Rate', value: 115, unit: 'bpm', timestamp: endTime.subtract(const Duration(hours: 1))), // Mock anomaly
        HealthDataPoint(dataType: 'Steps', value: 4500, unit: 'count', timestamp: endTime),
      ];
    }

    // Real implementation
    try {
      List<HealthDataPoint> points = [];
      for (var type in allTypes) {
        var data = await _health.getHealthDataFromTypes(
          startTime: startTime,
          endTime: endTime,
          types: [type],
        );
        for (var point in data) {
          points.add(HealthDataPoint(
            dataType: point.typeString,
            value: double.tryParse(point.value.toString()) ?? 0.0,
            unit: point.unitString,
            timestamp: point.dateFrom,
          ));
        }
      }
      return points;
    } catch (e) {
      debugPrint('Fetching Health Data Error: \$e');
      rethrow;
    }
  }
}
