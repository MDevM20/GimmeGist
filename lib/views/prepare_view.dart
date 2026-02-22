import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'package:ag_gimme_gist/services/appointment_repository.dart';
import 'package:ag_gimme_gist/services/med_gemma_service.dart';
import 'package:ag_gimme_gist/viewmodels/prepare_viewmodel.dart';
import 'package:ag_gimme_gist/viewmodels/settings_viewmodel.dart';

class PrepareView extends StatefulWidget {
  final String appointmentId;

  const PrepareView({super.key, required this.appointmentId});

  @override
  State<PrepareView> createState() => _PrepareViewState();
}

class _PrepareViewState extends State<PrepareView> {
  final PrepareViewModel _viewModel = PrepareViewModel();
  final SettingsViewModel _settings = SettingsViewModel();
  final AppointmentRepository _repository = AppointmentRepository();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _viewModel.loadQuestions(isMocked: _settings.isMocked);
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
      var updated = existing.copyWith(agendaPrepared: true);
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
          'Consultation Agenda',
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
            if (_viewModel.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }

            if (_viewModel.errorMessage != null) {
              return Center(child: Text(_viewModel.errorMessage!));
            }

            return Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Your 15-Minute Visit',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'High-yield questions prioritized for your time with the doctor.',
                    style: TextStyle(fontSize: 16, color: Colors.grey),
                  ),
                  const SizedBox(height: 24),
                  Expanded(
                    child: ListView.builder(
                      itemCount: _viewModel.questions.length,
                      itemBuilder: (context, index) {
                        return _buildQuestionCard(
                          _viewModel.questions[index],
                        );
                      },
                    ),
                  ),

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

  Widget _buildQuestionCard(StrategicQuestion sq) {
    final colorScheme = Theme.of(context).colorScheme;
    final isInsight = sq.isSecondaryOversight;

    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: Card(
        color: isInsight ? colorScheme.secondaryContainer : null,
        elevation: isInsight ? 2 : 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: isInsight
              ? BorderSide(color: colorScheme.secondary, width: 1.5)
              : BorderSide.none,
        ),
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(
                    isInsight ? Icons.visibility : Icons.menu_book,
                    color: isInsight
                        ? colorScheme.onSecondaryContainer
                        : colorScheme.primary,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    sq.category.toUpperCase(),
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                      color: isInsight
                          ? colorScheme.onSecondaryContainer
                          : colorScheme.primary,
                    ),
                  ),
                  const Spacer(),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                sq.question,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  height: 1.3,
                  color: isInsight
                      ? colorScheme.onSecondaryContainer
                      : colorScheme.onSurface,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
