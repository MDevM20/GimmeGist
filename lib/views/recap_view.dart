import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'package:ag_gimme_gist/models/appointment.dart';
import 'package:ag_gimme_gist/services/appointment_repository.dart';
import 'package:ag_gimme_gist/viewmodels/recap_viewmodel.dart';
import 'package:ag_gimme_gist/viewmodels/settings_viewmodel.dart';

/// Displays the visit recorder and recap summary.
///
/// When visiting from the hub, records audio and generates a recap.
/// When the appointment is already completed, shows the saved recap (read-only).
class RecapView extends StatefulWidget {
  final String appointmentId;

  const RecapView({super.key, required this.appointmentId});

  @override
  State<RecapView> createState() => _RecapViewState();
}

class _RecapViewState extends State<RecapView> {
  final RecapViewModel _viewModel = RecapViewModel();
  final SettingsViewModel _settings = SettingsViewModel();
  final AppointmentRepository _repository = AppointmentRepository();

  Appointment? _appointment;
  bool _isLoadingAppointment = false;

  @override
  void initState() {
    super.initState();
    _loadAppointment();
  }

  Future<void> _loadAppointment() async {
    _isLoadingAppointment = true;
    if (mounted) setState(() {});

    final all = await _repository.getAll();
    _appointment = all.where((a) => a.id == widget.appointmentId).firstOrNull;
    _isLoadingAppointment = false;
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _viewModel.dispose();
    _settings.dispose();
    super.dispose();
  }

  bool get _isReadOnly =>
      _appointment?.status == AppointmentStatus.completed;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _viewModel,
      builder: (context, _) {
        return PopScope(
          canPop: false,
          onPopInvokedWithResult: (didPop, _) {
            if (didPop) return;
            if (_viewModel.isRecording) {
              _showStopRecordingDialog(context);
            } else {
              context.go('/visit/${widget.appointmentId}');
            }
          },
          child: _buildContent(context),
        );
      },
    );
  }

  /// Asks the user to confirm leaving while recording is active.
  void _showStopRecordingDialog(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Recording in Progress'),
        content: const Text(
          'You are currently recording your visit. '
          'Leaving now will discard the recording. Are you sure?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Keep Recording'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              context.go('/visit/${widget.appointmentId}');
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Discard & Leave'),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    if (_isLoadingAppointment) {
      return Scaffold(
        backgroundColor: Colors.transparent,
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_appointment == null) {
      return Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => context.go('/'),
          ),
        ),
        body: const Center(child: Text('Visit not found.')),
      );
    }

    if (_isReadOnly) {
      return _buildReadOnlyScaffold(context);
    }
    return _buildLiveScaffold(context);
  }

  // ── Read-Only Mode ──

  Widget _buildReadOnlyScaffold(BuildContext context) {
    final appointment = _appointment!;
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text(
          'Visit Recap',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/visit/${widget.appointmentId}'),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Icon(Icons.person, color: colorScheme.primary, size: 28),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          appointment.doctorName,
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          appointment.reason,
                          style: TextStyle(
                            fontSize: 15,
                            color: colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                _formatDate(appointment.date),
                style: TextStyle(
                  fontSize: 13,
                  color: colorScheme.onSurfaceVariant.withValues(alpha: 0.7),
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'Post-Visit Summary',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 16),
              if (appointment.recapSummary != null)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20.0),
                    child: Text(
                      appointment.recapSummary!,
                      style: const TextStyle(fontSize: 16, height: 1.5),
                    ),
                  ),
                ),
              if (appointment.actionItems != null &&
                  appointment.actionItems!.isNotEmpty) ...[
                const SizedBox(height: 24),
                const Text(
                  'Action Items',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                ...appointment.actionItems!.map(
                  (item) => _buildListItem(item, Icons.check_box_outlined),
                ),
              ],
              if (appointment.followUps != null &&
                  appointment.followUps!.isNotEmpty) ...[
                const SizedBox(height: 24),
                const Text(
                  'Follow-ups',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                ...appointment.followUps!.map(
                  (item) => _buildListItem(item, Icons.event),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  // ── Live Mode ──

  Widget _buildLiveScaffold(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text(
          'Visit Recap',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/visit/${widget.appointmentId}'),
        ),
      ),
      body: SafeArea(
        child: ListenableBuilder(
          listenable: _viewModel,
          builder: (context, _) {
            if (_viewModel.isProcessing) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 24),
                    Text(
                      'MedGemma is analyzing the visit audio...',
                      style: TextStyle(
                        fontSize: 18,
                        color: Theme.of(context).colorScheme.primary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              );
            }

            if (_viewModel.errorMessage != null) {
              return Center(child: Text(_viewModel.errorMessage!));
            }

            return Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (_viewModel.recap == null) ...[
                    const Spacer(),
                    Icon(
                      _viewModel.isRecording ? Icons.mic : Icons.mic_none,
                      size: 80,
                      color: _viewModel.isRecording
                          ? Colors.red
                          : Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(height: 24),
                    Text(
                      _viewModel.isRecording
                          ? 'Recording Consultation...'
                          : 'Ready to Record Consultation',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Spacer(),
                    ElevatedButton.icon(
                      onPressed: () {
                        if (_viewModel.isRecording) {
                          _viewModel.stopRecordingAndProcess(
                            isMocked: _settings.isMocked,
                          );
                        } else {
                          _viewModel.startRecording();
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 20),
                        backgroundColor: _viewModel.isRecording
                            ? Colors.red.shade100
                            : Theme.of(context).colorScheme.primaryContainer,
                        foregroundColor: _viewModel.isRecording
                            ? Colors.red
                            : Theme.of(context)
                                .colorScheme
                                .onPrimaryContainer,
                      ),
                      icon: Icon(
                        _viewModel.isRecording
                            ? Icons.stop
                            : Icons.fiber_manual_record,
                      ),
                      label: Text(
                        _viewModel.isRecording
                            ? 'Stop & Generate Recap'
                            : 'Start Recording',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    if (!_viewModel.isRecording) ...[
                      const SizedBox(height: 12),
                      OutlinedButton(
                        onPressed: () => context.go(
                          '/visit/${widget.appointmentId}',
                        ),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: const Text(
                          'Return to Visit',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ] else ...[
                    const Text(
                      'Post-Visit Summary',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Expanded(
                      child: SingleChildScrollView(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Card(
                              child: Padding(
                                padding: const EdgeInsets.all(20.0),
                                child: Text(
                                  _viewModel.recap!.summary,
                                  style: const TextStyle(
                                    fontSize: 16,
                                    height: 1.5,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 24),
                            const Text(
                              'Action Items',
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 8),
                            ..._viewModel.recap!.actionItems.map(
                              (item) => _buildListItem(
                                item,
                                Icons.check_box_outlined,
                              ),
                            ),
                            const SizedBox(height: 24),
                            const Text(
                              'Follow-ups',
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 8),
                            ..._viewModel.recap!.followUps.map(
                              (item) => _buildListItem(item, Icons.event),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () => _saveAndGoToHub(),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      child: const Text(
                        'Done',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  /// Saves the completed recap to the appointment and navigates to the hub.
  Future<void> _saveAndGoToHub() async {
    if (_viewModel.recap != null && _appointment != null) {
      var updated = _appointment!.copyWith(
        visitRecorded: true,
        recapSummary: _viewModel.recap!.summary,
        actionItems: _viewModel.recap!.actionItems,
        followUps: _viewModel.recap!.followUps,
      );
      updated = updated.copyWith(status: updated.derivedStatus);
      await _repository.save(updated);
    }
    if (mounted) {
      context.go('/visit/${widget.appointmentId}');
    }
  }

  Widget _buildListItem(String text, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: Theme.of(context).colorScheme.primary, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 16, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
    final months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    ];
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }
}
