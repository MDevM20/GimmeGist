import 'package:json_annotation/json_annotation.dart';

part 'appointment.g.dart';

/// Represents the lifecycle status of a doctor visit.
enum AppointmentStatus {
  @JsonValue('draft')
  draft,
  @JsonValue('preparing')
  preparing,
  @JsonValue('visitReady')
  visitReady,
  @JsonValue('completed')
  completed,
}

/// A single doctor visit with per-step progress tracking.
@JsonSerializable()
class Appointment {
  final String id;
  final String doctorName;
  final String reason;
  final DateTime date;
  final AppointmentStatus status;

  // Per-step completion flags for non-linear progress.
  final bool dataIngested;
  final bool gistGenerated;
  final bool agendaPrepared;
  final bool visitRecorded;

  // Recap data — populated after the visit is recorded.
  final String? recapSummary;
  final List<String>? actionItems;
  final List<String>? followUps;

  final List<IngestedHealthMetric>? ingestedHealthData;
  final List<IngestedFile>? uploadedFiles;

  const Appointment({
    required this.id,
    required this.doctorName,
    required this.reason,
    required this.date,
    this.status = AppointmentStatus.draft,
    this.dataIngested = false,
    this.gistGenerated = false,
    this.agendaPrepared = false,
    this.visitRecorded = false,
    this.recapSummary,
    this.actionItems,
    this.followUps,
    this.ingestedHealthData,
    this.uploadedFiles,
  });

  /// Creates a copy with the specified fields overridden.
  Appointment copyWith({
    String? doctorName,
    String? reason,
    DateTime? date,
    AppointmentStatus? status,
    bool? dataIngested,
    bool? gistGenerated,
    bool? agendaPrepared,
    bool? visitRecorded,
    String? recapSummary,
    List<String>? actionItems,
    List<String>? followUps,
    List<IngestedHealthMetric>? ingestedHealthData,
    List<IngestedFile>? uploadedFiles,
  }) {
    return Appointment(
      id: id,
      doctorName: doctorName ?? this.doctorName,
      reason: reason ?? this.reason,
      date: date ?? this.date,
      status: status ?? this.status,
      dataIngested: dataIngested ?? this.dataIngested,
      gistGenerated: gistGenerated ?? this.gistGenerated,
      agendaPrepared: agendaPrepared ?? this.agendaPrepared,
      visitRecorded: visitRecorded ?? this.visitRecorded,
      recapSummary: recapSummary ?? this.recapSummary,
      actionItems: actionItems ?? this.actionItems,
      followUps: followUps ?? this.followUps,
      ingestedHealthData: ingestedHealthData ?? this.ingestedHealthData,
      uploadedFiles: uploadedFiles ?? this.uploadedFiles,
    );
  }

  /// Derives the correct status from the current step flags.
  AppointmentStatus get derivedStatus {
    if (recapSummary != null) return AppointmentStatus.completed;
    if (dataIngested || gistGenerated || agendaPrepared) {
      if (agendaPrepared) return AppointmentStatus.visitReady;
      return AppointmentStatus.preparing;
    }
    return AppointmentStatus.draft;
  }

  factory Appointment.fromJson(Map<String, dynamic> json) =>
      _$AppointmentFromJson(json);

  Map<String, dynamic> toJson() => _$AppointmentToJson(this);
}

@JsonSerializable()
class IngestedHealthMetric {
  final String type;
  final double value;
  final String unit;
  final String timestamp;

  const IngestedHealthMetric({
    required this.type,
    required this.value,
    required this.unit,
    required this.timestamp,
  });

  factory IngestedHealthMetric.fromJson(Map<String, dynamic> json) =>
      _$IngestedHealthMetricFromJson(json);

  Map<String, dynamic> toJson() => _$IngestedHealthMetricToJson(this);
}

@JsonSerializable()
class IngestedFile {
  final String name;
  final int size;
  final String? extension;

  const IngestedFile({
    required this.name,
    required this.size,
    this.extension,
  });

  factory IngestedFile.fromJson(Map<String, dynamic> json) =>
      _$IngestedFileFromJson(json);

  Map<String, dynamic> toJson() => _$IngestedFileToJson(this);
}
