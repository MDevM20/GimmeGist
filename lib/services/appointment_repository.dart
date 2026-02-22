import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import 'package:ag_gimme_gist/models/appointment.dart';

/// Local persistence for appointments using SharedPreferences.
class AppointmentRepository {
  static const _storageKey = 'appointments';

  /// Legacy status values from the old enum that need migration.
  static const _statusMigration = {
    'inProgress': 'preparing',
    'upcoming': 'draft',
  };

  /// Returns all saved appointments, sorted newest-first by date.
  Future<List<Appointment>> getAll() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw == null || raw.isEmpty) return [];

    final List<dynamic> decoded = jsonDecode(raw) as List<dynamic>;
    final appointments = <Appointment>[];
    for (final e in decoded) {
      try {
        final map = e as Map<String, dynamic>;
        // Migrate legacy status values.
        if (map.containsKey('status') &&
            _statusMigration.containsKey(map['status'])) {
          map['status'] = _statusMigration[map['status']];
        }
        appointments.add(Appointment.fromJson(map));
      } catch (_) {
        // Skip entries that cannot be deserialized.
      }
    }
    appointments.sort((a, b) => b.date.compareTo(a.date));

    return appointments;
  }

  /// Persists or upserts a single appointment.
  Future<void> save(Appointment appointment) async {
    final all = await getAll();
    final index = all.indexWhere((a) => a.id == appointment.id);
    if (index >= 0) {
      all[index] = appointment;
    } else {
      all.insert(0, appointment);
    }
    await _persist(all);
  }

  /// Deletes an appointment by id.
  Future<void> delete(String id) async {
    final all = await getAll();
    all.removeWhere((a) => a.id == id);
    await _persist(all);
  }

  Future<void> _persist(List<Appointment> appointments) async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = jsonEncode(appointments.map((a) => a.toJson()).toList());
    await prefs.setString(_storageKey, encoded);
  }
}
