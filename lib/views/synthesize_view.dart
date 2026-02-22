import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'package:ag_gimme_gist/services/appointment_repository.dart';
import 'package:ag_gimme_gist/services/med_gemma_service.dart';
import 'package:ag_gimme_gist/viewmodels/settings_viewmodel.dart';
import 'package:ag_gimme_gist/viewmodels/synthesize_viewmodel.dart';

class SynthesizeView extends StatefulWidget {
  final String appointmentId;

  const SynthesizeView({super.key, required this.appointmentId});

  @override
  State<SynthesizeView> createState() => _SynthesizeViewState();
}

class _SynthesizeViewState extends State<SynthesizeView> {
  final SynthesizeViewModel _viewModel = SynthesizeViewModel();
  final SettingsViewModel _settings = SettingsViewModel();
  final AppointmentRepository _repository = AppointmentRepository();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _viewModel.evaluateData(isMocked: _settings.isMocked);
    });
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
      var updated = existing.copyWith(gistGenerated: true);
      updated = updated.copyWith(status: updated.derivedStatus);
      await _repository.save(updated);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) context.go('/visit/${widget.appointmentId}');
      },
      child: Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text(
          'The Gist',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/visit/${widget.appointmentId}'),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () =>
                _viewModel.evaluateData(isMocked: _settings.isMocked),
          ),
        ],
      ),
      body: SafeArea(
        child: ListenableBuilder(
          listenable: _viewModel,
          builder: (context, _) {
            if (_viewModel.isLoading) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 24),
                    Text(
                      'MedGemma is analyzing your data...',
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

            if (_viewModel.summary == null) {
              return const Center(child: Text('No data generated.'));
            }

            final summary = _viewModel.summary!;

            return SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Your Clinical Summary',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // The Gist Card
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildGistRow(
                            context,
                            Icons.medical_information,
                            'The Cause',
                            summary.cause,
                          ),
                          const Divider(height: 32),
                          _buildGistRow(
                            context,
                            Icons.location_on,
                            'The Location',
                            summary.location,
                          ),
                          const Divider(height: 32),
                          _buildGistRow(
                            context,
                            Icons.flag,
                            'The Goal',
                            summary.goal,
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 32),

                  // Anomaly Alerts
                  if (_viewModel.anomalies.isNotEmpty) ...[
                    const Text(
                      'Anomaly Alerts',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    ..._viewModel.anomalies
                        .map((anomaly) => _buildAnomalyCard(anomaly)),
                    const SizedBox(height: 24),
                  ],

                  // Save & Return
                  ElevatedButton(
                    onPressed: () async {
                      await _saveProgress();
                      if (context.mounted) {
                        context.go('/visit/${widget.appointmentId}');
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      backgroundColor:
                          Theme.of(context).colorScheme.primaryContainer,
                      foregroundColor:
                          Theme.of(context).colorScheme.onPrimaryContainer,
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
      ),
    ),
    );
  }

  Widget _buildGistRow(
    BuildContext context,
    IconData icon,
    String title,
    String content,
  ) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: Theme.of(context).colorScheme.primary, size: 28),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                content,
                style: const TextStyle(fontSize: 16, height: 1.5),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildAnomalyCard(AnomalyAlert anomaly) {
    final colorScheme = Theme.of(context).colorScheme;
    final isHigh = anomaly.isHighPriority;

    return Card(
      color: isHigh
          ? colorScheme.errorContainer
          : colorScheme.surfaceContainerHighest,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: isHigh
            ? BorderSide(color: colorScheme.error, width: 1.5)
            : BorderSide.none,
      ),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              isHigh ? Icons.warning_amber_rounded : Icons.info_outline,
              color: isHigh ? colorScheme.onErrorContainer : colorScheme.primary,
              size: 32,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    anomaly.title,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: isHigh
                          ? colorScheme.onErrorContainer
                          : colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    anomaly.description,
                    style: TextStyle(
                      fontSize: 15,
                      height: 1.4,
                      color: isHigh
                          ? colorScheme.onErrorContainer
                          : colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    anomaly.timestamp,
                    style: TextStyle(
                      fontSize: 12,
                      color: isHigh
                          ? colorScheme.onErrorContainer
                              .withValues(alpha: 0.7)
                          : colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
