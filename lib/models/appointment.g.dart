// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'appointment.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Appointment _$AppointmentFromJson(Map<String, dynamic> json) => Appointment(
  id: json['id'] as String,
  doctorName: json['doctorName'] as String,
  reason: json['reason'] as String,
  date: DateTime.parse(json['date'] as String),
  status:
      $enumDecodeNullable(_$AppointmentStatusEnumMap, json['status']) ??
      AppointmentStatus.draft,
  dataIngested: json['dataIngested'] as bool? ?? false,
  gistGenerated: json['gistGenerated'] as bool? ?? false,
  agendaPrepared: json['agendaPrepared'] as bool? ?? false,
  visitRecorded: json['visitRecorded'] as bool? ?? false,
  recapSummary: json['recapSummary'] as String?,
  actionItems: (json['actionItems'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  followUps: (json['followUps'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  ingestedHealthData: (json['ingestedHealthData'] as List<dynamic>?)
      ?.map((e) => IngestedHealthMetric.fromJson(e as Map<String, dynamic>))
      .toList(),
  uploadedFiles: (json['uploadedFiles'] as List<dynamic>?)
      ?.map((e) => IngestedFile.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$AppointmentToJson(Appointment instance) =>
    <String, dynamic>{
      'id': instance.id,
      'doctorName': instance.doctorName,
      'reason': instance.reason,
      'date': instance.date.toIso8601String(),
      'status': _$AppointmentStatusEnumMap[instance.status]!,
      'dataIngested': instance.dataIngested,
      'gistGenerated': instance.gistGenerated,
      'agendaPrepared': instance.agendaPrepared,
      'visitRecorded': instance.visitRecorded,
      'recapSummary': instance.recapSummary,
      'actionItems': instance.actionItems,
      'followUps': instance.followUps,
      'ingestedHealthData': instance.ingestedHealthData,
      'uploadedFiles': instance.uploadedFiles,
    };

const _$AppointmentStatusEnumMap = {
  AppointmentStatus.draft: 'draft',
  AppointmentStatus.preparing: 'preparing',
  AppointmentStatus.visitReady: 'visitReady',
  AppointmentStatus.completed: 'completed',
};

IngestedHealthMetric _$IngestedHealthMetricFromJson(
  Map<String, dynamic> json,
) => IngestedHealthMetric(
  type: json['type'] as String,
  value: (json['value'] as num).toDouble(),
  unit: json['unit'] as String,
  timestamp: json['timestamp'] as String,
);

Map<String, dynamic> _$IngestedHealthMetricToJson(
  IngestedHealthMetric instance,
) => <String, dynamic>{
  'type': instance.type,
  'value': instance.value,
  'unit': instance.unit,
  'timestamp': instance.timestamp,
};

IngestedFile _$IngestedFileFromJson(Map<String, dynamic> json) => IngestedFile(
  name: json['name'] as String,
  size: (json['size'] as num).toInt(),
  extension: json['extension'] as String?,
);

Map<String, dynamic> _$IngestedFileToJson(IngestedFile instance) =>
    <String, dynamic>{
      'name': instance.name,
      'size': instance.size,
      'extension': instance.extension,
    };
