import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:file_picker/file_picker.dart';

import 'package:ag_gimme_gist/services/appointment_repository.dart';
import 'package:ag_gimme_gist/models/appointment.dart';
import 'package:ag_gimme_gist/viewmodels/ingest_viewmodel.dart';
import 'package:ag_gimme_gist/viewmodels/settings_viewmodel.dart';

class IngestView extends StatefulWidget {
  final String appointmentId;

  const IngestView({super.key, required this.appointmentId});

  @override
  State<IngestView> createState() => _IngestViewState();
}

class _IngestViewState extends State<IngestView> {
  final IngestViewModel _viewModel = IngestViewModel();
  final SettingsViewModel _settings = SettingsViewModel();
  final AppointmentRepository _repository = AppointmentRepository();

  @override
  void initState() {
    super.initState();
    _loadInitialState();
  }

  Future<void> _loadInitialState() async {
    final all = await _repository.getAll();
    final existing = all.where((a) => a.id == widget.appointmentId).firstOrNull;
    if (existing != null && mounted) {
      _viewModel.initialize(existing);
    }
  }

  @override
  void dispose() {
    _viewModel.dispose();
    _settings.dispose();
    super.dispose();
  }

  Future<void> _saveProgress() async {
    final all = await _repository.getAll();
    final existing = all.where((a) => a.id == widget.appointmentId).firstOrNull;
    if (existing != null) {
      var updated = existing.copyWith(
        dataIngested: true,
        ingestedHealthData: _viewModel.recentData.map((d) => 
            IngestedHealthMetric(type: d.dataType, value: d.value, unit: d.unit, timestamp: d.timestamp.toIso8601String())
        ).toList(),
        uploadedFiles: _viewModel.uploadedFiles.map((f) => 
            IngestedFile(name: f.name, size: f.size, extension: f.extension)
        ).toList(),
      );
      updated = updated.copyWith(status: updated.derivedStatus);
      await _repository.save(updated);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) context.pop();
      },
      child: Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text(
          'Ingest Data',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
        actions: [
          ListenableBuilder(
            listenable: _settings,
            builder: (context, _) {
              return IconButton(
                icon: Icon(
                  _settings.isMocked ? Icons.bug_report : Icons.cloud_done,
                  color: _settings.isMocked ? Colors.orange : Colors.green,
                ),
                tooltip: _settings.isMocked
                    ? 'Mocked Mode Active'
                    : 'Real Mode Active',
                onPressed: () {
                  _settings.toggleMode(
                    _settings.isMocked ? AppMode.real : AppMode.mocked,
                  );
                },
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: ListenableBuilder(
                listenable: _viewModel,
                builder: (context, _) {
                  return ConstrainedBox(
                    constraints: BoxConstraints(
                      minHeight: constraints.maxHeight - 48,
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text(
                          'Gather Your Data',
                          style: TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.w800,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          'Sync wearable data and upload clinical reports.',
                          style: TextStyle(fontSize: 18, color: Colors.grey),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 48),

                        if (_viewModel.errorMessage != null) ...[
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: Theme.of(context).colorScheme.errorContainer,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  Icons.error_outline,
                                  color: Theme.of(context).colorScheme.error,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    _viewModel.errorMessage!,
                                    style: TextStyle(
                                      color: Theme.of(context).colorScheme.onErrorContainer,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 24),
                        ],

                        // Wearable Data Card
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(24.0),
                            child: Column(
                              children: [
                                const Icon(
                                  Icons.favorite,
                                  size: 48,
                                  color: Colors.pinkAccent,
                                ),
                                const SizedBox(height: 16),
                                const Text(
                                  'Wearable Data',
                                  style: TextStyle(
                                    fontSize: 22,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                const Text(
                                  'Sync step count, heart rate, and vitals from Health Connect.',
                                  textAlign: TextAlign.center,
                                ),
                                const SizedBox(height: 24),
                                  ElevatedButton.icon(
                                    onPressed: (_viewModel.isSyncingHealth || _viewModel.isUploading)
                                        ? null
                                        : () async {
                                            final DateTimeRange? range = await showDateRangePicker(
                                              context: context,
                                              firstDate: DateTime.now().subtract(const Duration(days: 365)),
                                              lastDate: DateTime.now(),
                                            );
                                            if (range != null && context.mounted) {
                                              _viewModel.syncWearableData(
                                                isMocked: _settings.isMocked,
                                                start: range.start,
                                                end: range.end,
                                              );
                                            }
                                          },
                                    icon: _viewModel.isSyncingHealth
                                        ? const SizedBox(
                                            width: 20,
                                            height: 20,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                            ),
                                          )
                                        : const Icon(Icons.sync),
                                    label: const Text('Sync Health Connect'),
                                ),
                              ],
                            ),
                          ),
                        ),

                        const SizedBox(height: 24),

                        // Medical Records Card
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(24.0),
                            child: Column(
                              children: [
                                const Icon(
                                  Icons.document_scanner,
                                  size: 48,
                                  color: Colors.blueAccent,
                                ),
                                const SizedBox(height: 16),
                                const Text(
                                  'Diagnostic Reports',
                                  style: TextStyle(
                                    fontSize: 22,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                const Text(
                                  'Upload PDFs or images of your clinical reports for translation.',
                                  textAlign: TextAlign.center,
                                ),
                                const SizedBox(height: 24),
                                  ElevatedButton.icon(
                                    onPressed: (_viewModel.isSyncingHealth || _viewModel.isUploading)
                                        ? null
                                        : () => _viewModel.uploadDiagnosticReport(),
                                    icon: _viewModel.isUploading
                                        ? const SizedBox(
                                            width: 20,
                                            height: 20,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                            ),
                                          )
                                        : const Icon(Icons.upload_file),
                                    label: const Text('Upload Report'),
                                ),
                              ],
                            ),
                          ),
                        ),

                        const SizedBox(height: 32),

                        if (_viewModel.uploadedFiles.isNotEmpty) ...[
                          Card(
                            elevation: 2,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(16.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  const Text(
                                    'Selected Reports',
                                    style: TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  const Divider(),
                                  ..._viewModel.uploadedFiles.map((file) {
                                    return Padding(
                                      padding: const EdgeInsets.symmetric(vertical: 8.0),
                                      child: Row(
                                        children: [
                                          Icon(
                                            file.extension?.toLowerCase() == 'pdf' 
                                                ? Icons.picture_as_pdf 
                                                : Icons.image,
                                            color: Theme.of(context).colorScheme.primary,
                                          ),
                                          const SizedBox(width: 12),
                                          Expanded(
                                            child: Text(
                                              file.name,
                                              style: const TextStyle(fontWeight: FontWeight.w600),
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                          Text(
                                            '${(file.size / 1024).toStringAsFixed(0)} KB',
                                            style: const TextStyle(color: Colors.grey),
                                          ),
                                        ],
                                      ),
                                    );
                                  }),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 24),
                        ],

                        if (_viewModel.recentData.isNotEmpty) ...[
                          const Icon(
                            Icons.check_circle,
                            color: Colors.green,
                            size: 48,
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Data Synced Successfully',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: Colors.green,
                            ),
                          ),
                          const SizedBox(height: 16),
                          Card(
                            elevation: 2,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(16.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  const Text(
                                    'Latest Readings',
                                    style: TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  const Divider(),
                                  ..._viewModel.latestDataByType.values.map((dt) {
                                    // Capitalize and format data type string
                                    final formattedType = dt.dataType
                                        .split('_')
                                        .map((word) => word.isNotEmpty
                                            ? '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}'
                                            : '')
                                        .join(' ');
                                        
                                    return Padding(
                                      padding: const EdgeInsets.symmetric(vertical: 4.0),
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            formattedType,
                                            style: const TextStyle(
                                              fontWeight: FontWeight.w600,
                                              color: Colors.black87,
                                            ),
                                          ),
                                          Text(
                                            '${dt.value.toStringAsFixed(2).replaceAll(RegExp(r"([.]*0+)(?!.*\d)"), "")} ${dt.unit}',
                                            style: TextStyle(
                                              fontSize: 16,
                                              color: Theme.of(context).colorScheme.primary,
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                        ],
                                      ),
                                    );
                                  }),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 24),
                        ],

                        // Save & Return
                        ElevatedButton(
                          onPressed: () async {
                            await _saveProgress();
                            if (context.mounted) {
                              context.pop();
                            }
                          },
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            backgroundColor:
                                Theme.of(context).colorScheme.primaryContainer,
                            foregroundColor: Theme.of(context)
                                .colorScheme
                                .onPrimaryContainer,
                          ),
                          child: const Text(
                            'Save & Return',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            );
          },
        ),
      ),
    ),
    );
  }
}
