import 'package:flutter/material.dart';

import 'package:ag_gimme_gist/models/appointment.dart';
import 'package:ag_gimme_gist/services/appointment_repository.dart';

/// Drives the visit detail hub, managing a single appointment's lifecycle.
class VisitDetailViewModel extends ChangeNotifier {
  final AppointmentRepository _repository = AppointmentRepository();

  Appointment? _appointment;
  Appointment? get appointment => _appointment;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  /// Loads an appointment by id.
  Future<void> load(String id) async {
    _isLoading = true;
    notifyListeners();

    final all = await _repository.getAll();
    _appointment = all.where((a) => a.id == id).firstOrNull;

    _isLoading = false;
    notifyListeners();
  }

  /// Marks a step complete and auto-derives the new status.
  Future<void> markStepComplete({
    bool? dataIngested,
    bool? gistGenerated,
    bool? agendaPrepared,
    bool? visitRecorded,
    String? recapSummary,
    List<String>? actionItems,
    List<String>? followUps,
  }) async {
    if (_appointment == null) return;

    var updated = _appointment!.copyWith(
      dataIngested: dataIngested,
      gistGenerated: gistGenerated,
      agendaPrepared: agendaPrepared,
      visitRecorded: visitRecorded,
      recapSummary: recapSummary,
      actionItems: actionItems,
      followUps: followUps,
    );

    // Auto-derive status from step flags.
    updated = updated.copyWith(status: updated.derivedStatus);

    await _repository.save(updated);
    _appointment = updated;
    notifyListeners();
  }

  /// Updates the appointment header info (doctor name, reason, date).
  Future<void> updateInfo({
    String? doctorName,
    String? reason,
    DateTime? date,
  }) async {
    if (_appointment == null) return;

    final updated = _appointment!.copyWith(
      doctorName: doctorName,
      reason: reason,
      date: date,
    );

    await _repository.save(updated);
    _appointment = updated;
    notifyListeners();
  }
}
