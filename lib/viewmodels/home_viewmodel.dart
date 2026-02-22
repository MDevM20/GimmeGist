import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import 'package:ag_gimme_gist/models/appointment.dart';
import 'package:ag_gimme_gist/services/appointment_repository.dart';

/// Drives the home dashboard, managing the list of appointments.
class HomeViewModel extends ChangeNotifier {
  final AppointmentRepository _repository = AppointmentRepository();
  static const _uuid = Uuid();

  List<Appointment> _appointments = [];
  List<Appointment> get appointments => _appointments;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  /// Loads all appointments from local storage, sorted by date.
  Future<void> loadAppointments() async {
    _isLoading = true;
    notifyListeners();

    _appointments = await _repository.getAll();
    _sortByDate();

    _isLoading = false;
    notifyListeners();
  }

  /// Creates a new draft appointment and returns its id for navigation.
  Future<String> startNewAppointment({
    required String doctorName,
    required String reason,
    required DateTime date,
  }) async {
    final appointment = Appointment(
      id: _uuid.v4(),
      doctorName: doctorName,
      reason: reason,
      date: date,
      status: AppointmentStatus.draft,
    );

    await _repository.save(appointment);
    _appointments.add(appointment);
    _sortByDate();
    notifyListeners();

    return appointment.id;
  }

  /// Deletes an appointment by id.
  Future<void> deleteAppointment(String id) async {
    await _repository.delete(id);
    _appointments.removeWhere((a) => a.id == id);
    notifyListeners();
  }

  /// Sorts appointments by date, soonest first.
  void _sortByDate() {
    _appointments.sort((a, b) => a.date.compareTo(b.date));
  }
}
