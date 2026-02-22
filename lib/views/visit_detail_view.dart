import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'package:ag_gimme_gist/models/appointment.dart';
import 'package:ag_gimme_gist/viewmodels/visit_detail_viewmodel.dart';

/// Central hub for a single appointment showing header + journey steps.
class VisitDetailView extends StatefulWidget {
  final String appointmentId;

  const VisitDetailView({super.key, required this.appointmentId});

  @override
  State<VisitDetailView> createState() => _VisitDetailViewState();
}

class _VisitDetailViewState extends State<VisitDetailView> {
  final VisitDetailViewModel _viewModel = VisitDetailViewModel();
  final TextEditingController _doctorController = TextEditingController();
  final TextEditingController _reasonController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadAppointment();
  }

  Future<void> _loadAppointment() async {
    await _viewModel.load(widget.appointmentId);
    if (_viewModel.appointment != null) {
      _doctorController.text = _viewModel.appointment!.doctorName;
      _reasonController.text = _viewModel.appointment!.reason;
    }
  }

  @override
  void dispose() {
    _viewModel.dispose();
    _doctorController.dispose();
    _reasonController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) context.go('/');
      },
      child: Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text(
          'Visit Details',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/'),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: () => _loadAppointment(),
          ),
        ],
      ),
      body: SafeArea(
        child: ListenableBuilder(
          listenable: _viewModel,
          builder: (context, _) {
            if (_viewModel.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }

            final appointment = _viewModel.appointment;
            if (appointment == null) {
              return const Center(child: Text('Visit not found.'));
            }

            return SingleChildScrollView(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _buildHeader(context, appointment),
                  const SizedBox(height: 28),
                  _buildSectionTitle(context, 'Journey'),
                  const SizedBox(height: 16),
                  _buildStepCard(
                    context,
                    icon: Icons.favorite,
                    iconColor: Colors.pinkAccent,
                    title: 'Ingest Data',
                    subtitle: 'Sync wearables & upload reports',
                    isDone: appointment.dataIngested,
                    isAvailable: true,
                    onTap: () async {
                      await context.push('/visit/${widget.appointmentId}/ingest');
                      _loadAppointment();
                    },
                  ),
                  _buildStepConnector(context, appointment.dataIngested),
                  _buildStepCard(
                    context,
                    icon: Icons.auto_awesome,
                    iconColor: Colors.deepPurpleAccent,
                    title: 'Clinical Gist',
                    subtitle: 'AI summary of your health data',
                    isDone: appointment.gistGenerated,
                    isAvailable: appointment.dataIngested,
                    onTap: appointment.dataIngested
                        ? () async {
                            await context.push('/visit/${widget.appointmentId}/synthesize');
                            _loadAppointment();
                          }
                        : null,
                  ),
                  _buildStepConnector(context, appointment.gistGenerated),
                  _buildStepCard(
                    context,
                    icon: Icons.menu_book,
                    iconColor: Colors.teal,
                    title: 'Consultation Agenda',
                    subtitle: 'Strategic questions for your visit',
                    isDone: appointment.agendaPrepared,
                    isAvailable: appointment.gistGenerated,
                    onTap: appointment.gistGenerated
                        ? () async {
                            await context.push('/visit/${widget.appointmentId}/prepare');
                            _loadAppointment();
                          }
                        : null,
                  ),
                  _buildStepConnector(context, appointment.agendaPrepared),
                  _buildStepCard(
                    context,
                    icon: Icons.mic,
                    iconColor: Colors.redAccent,
                    title: 'Visit Recap',
                    subtitle: 'Record audio & generate summary',
                    isDone: appointment.status == AppointmentStatus.completed,
                    isAvailable: true,
                    onTap: () async {
                      await context.push('/visit/${widget.appointmentId}/recap');
                      _loadAppointment();
                    },
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

  // ── Header ──

  Widget _buildHeader(BuildContext context, Appointment appointment) {
    final colorScheme = Theme.of(context).colorScheme;
    final isEditable = appointment.status != AppointmentStatus.completed;

    final statusColor = switch (appointment.status) {
      AppointmentStatus.completed => Colors.green,
      AppointmentStatus.visitReady => Colors.blue,
      AppointmentStatus.preparing => Colors.orange,
      AppointmentStatus.draft => colorScheme.onSurfaceVariant,
    };
    final statusLabel = switch (appointment.status) {
      AppointmentStatus.completed => 'Completed',
      AppointmentStatus.visitReady => 'Ready for Visit',
      AppointmentStatus.preparing => 'Preparing',
      AppointmentStatus.draft => 'Draft',
    };

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.person, color: colorScheme.primary, size: 28),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    appointment.doctorName,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                if (isEditable)
                  IconButton(
                    icon: const Icon(Icons.edit_outlined, size: 20),
                    onPressed: () => _showEditSheet(context, appointment),
                    tooltip: 'Edit details',
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              appointment.reason,
              style: TextStyle(
                fontSize: 16,
                color: colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(
                  Icons.calendar_today,
                  size: 14,
                  color: colorScheme.onSurfaceVariant.withValues(alpha: 0.7),
                ),
                const SizedBox(width: 6),
                Text(
                  _formatDate(appointment.date),
                  style: TextStyle(
                    fontSize: 13,
                    color: colorScheme.onSurfaceVariant.withValues(alpha: 0.7),
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    statusLabel,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: statusColor,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ── Step Cards ──

  Widget _buildSectionTitle(BuildContext context, String title) {
    return Text(
      title,
      style: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.bold,
        color: Theme.of(context).colorScheme.onSurface,
      ),
    );
  }

  Widget _buildStepCard(
    BuildContext context, {
    required IconData icon,
    required Color iconColor,
    required String title,
    required String subtitle,
    required bool isDone,
    required bool isAvailable,
    required VoidCallback? onTap,
  }) {
    final colorScheme = Theme.of(context).colorScheme;
    final isLocked = !isAvailable && !isDone;

    return Card(
      elevation: isLocked ? 1 : 4,
      color: isDone
          ? colorScheme.primaryContainer.withValues(alpha: 0.4)
          : isLocked
              ? colorScheme.surfaceContainerHighest.withValues(alpha: 0.5)
              : null,
      child: InkWell(
        onTap: isLocked ? null : onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: isLocked
                      ? colorScheme.onSurface.withValues(alpha: 0.08)
                      : iconColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  isDone ? Icons.check_circle : icon,
                  color: isDone
                      ? Colors.green
                      : isLocked
                          ? colorScheme.onSurface.withValues(alpha: 0.3)
                          : iconColor,
                  size: 28,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                        color: isLocked
                            ? colorScheme.onSurface.withValues(alpha: 0.4)
                            : colorScheme.onSurface,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      isDone
                          ? 'Completed ✓'
                          : isLocked
                              ? 'Complete previous step first'
                              : subtitle,
                      style: TextStyle(
                        fontSize: 13,
                        color: isDone
                            ? Colors.green
                            : isLocked
                                ? colorScheme.onSurface.withValues(alpha: 0.3)
                                : colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
              if (!isLocked)
                Icon(
                  Icons.chevron_right,
                  color: colorScheme.onSurfaceVariant,
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStepConnector(BuildContext context, bool isDone) {
    return Padding(
      padding: const EdgeInsets.only(left: 43.0),
      child: SizedBox(
        height: 24,
        child: VerticalDivider(
          width: 2,
          thickness: 2,
          color: isDone
              ? Colors.green.withValues(alpha: 0.5)
              : Theme.of(context)
                  .colorScheme
                  .onSurface
                  .withValues(alpha: 0.12),
        ),
      ),
    );
  }

  // ── Edit Sheet ──

  void _showEditSheet(BuildContext context, Appointment appointment) {
    _doctorController.text = appointment.doctorName;
    _reasonController.text = appointment.reason;

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (sheetContext) {
        return Padding(
          padding: EdgeInsets.fromLTRB(
            24,
            24,
            24,
            MediaQuery.of(sheetContext).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Edit Visit',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: _doctorController,
                decoration: const InputDecoration(
                  labelText: 'Doctor Name',
                  prefixIcon: Icon(Icons.person),
                  border: OutlineInputBorder(),
                ),
                textCapitalization: TextCapitalization.words,
                autofocus: true,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _reasonController,
                decoration: const InputDecoration(
                  labelText: 'Reason for Visit',
                  prefixIcon: Icon(Icons.note),
                  border: OutlineInputBorder(),
                ),
                textCapitalization: TextCapitalization.sentences,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () {
                  final doctor = _doctorController.text.trim();
                  final reason = _reasonController.text.trim();
                  if (doctor.isEmpty || reason.isEmpty) return;

                  Navigator.of(sheetContext).pop();
                  _viewModel.updateInfo(
                    doctorName: doctor,
                    reason: reason,
                  );
                },
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text(
                  'Save',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        );
      },
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
