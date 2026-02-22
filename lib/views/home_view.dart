import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'package:ag_gimme_gist/models/appointment.dart';
import 'package:ag_gimme_gist/viewmodels/home_viewmodel.dart';
import 'package:ag_gimme_gist/viewmodels/settings_viewmodel.dart';

class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  final HomeViewModel _viewModel = HomeViewModel();
  final SettingsViewModel _settings = SettingsViewModel();
  final TextEditingController _doctorController = TextEditingController();
  final TextEditingController _reasonController = TextEditingController();
  DateTime _selectedDate = DateTime.now();

  @override
  void initState() {
    super.initState();
    _viewModel.loadAppointments();
  }

  @override
  void dispose() {
    _viewModel.dispose();
    _settings.dispose();
    _doctorController.dispose();
    _reasonController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text(
          'GimmeGist',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 24),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          ListenableBuilder(
            listenable: _settings,
            builder: (context, _) {
              return IconButton(
                icon: Icon(
                  _settings.isMocked ? Icons.bug_report : Icons.cloud_done,
                  color: _settings.isMocked ? Colors.orange : Colors.green,
                ),
                tooltip:
                    _settings.isMocked ? 'Mocked Mode' : 'Real Mode',
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
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showNewAppointmentSheet(context),
        icon: const Icon(Icons.add),
        label: const Text('New Visit'),
      ),
      body: SafeArea(
        child: ListenableBuilder(
          listenable: _viewModel,
          builder: (context, _) {
            if (_viewModel.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }

            if (_viewModel.appointments.isEmpty) {
              return _buildEmptyState(context, colorScheme);
            }

            return _buildAppointmentList(context, colorScheme);
          },
        ),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context, ColorScheme colorScheme) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(48.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.medical_services_outlined,
              size: 96,
              color: colorScheme.primary.withValues(alpha: 0.3),
            ),
            const SizedBox(height: 24),
            Text(
              'No visits yet',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.w800,
                color: colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Tap the button below to prepare for your first doctor visit with AI-powered insights.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: colorScheme.onSurfaceVariant,
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAppointmentList(BuildContext context, ColorScheme colorScheme) {
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
      itemCount: _viewModel.appointments.length,
      itemBuilder: (context, index) {
        final appointment = _viewModel.appointments[index];
        return _buildAppointmentCard(context, appointment, colorScheme);
      },
    );
  }

  Widget _buildAppointmentCard(
    BuildContext context,
    Appointment appointment,
    ColorScheme colorScheme,
  ) {
    final isCompleted = appointment.status == AppointmentStatus.completed;
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

    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: () {
            // All appointments go to the hub
            context.go('/visit/${appointment.id}');
          },
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      isCompleted
                          ? Icons.check_circle
                          : Icons.calendar_today,
                      color: statusColor,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        appointment.doctorName,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
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
                const SizedBox(height: 8),
                Text(
                  appointment.reason,
                  style: TextStyle(
                    fontSize: 15,
                    color: colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Icon(
                      Icons.event,
                      size: 16,
                      color: colorScheme.primary.withValues(alpha: 0.7),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      _formatDate(appointment.date),
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: colorScheme.primary.withValues(alpha: 0.8),
                      ),
                    ),
                  ],
                ),
                if (isCompleted && appointment.recapSummary != null) ...[
                  const Divider(height: 24),
                  Text(
                    appointment.recapSummary!,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 14,
                      color: colorScheme.onSurfaceVariant,
                      height: 1.4,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showNewAppointmentSheet(BuildContext context) {
    _doctorController.clear();
    _reasonController.clear();
    _selectedDate = DateTime.now();

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (sheetContext, setSheetState) {
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
                    'New Visit',
                    style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 24),
                  TextField(
                    controller: _doctorController,
                    decoration: const InputDecoration(
                      labelText: 'Doctor Name',
                      hintText: 'e.g. Dr. Smith',
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
                      hintText: 'e.g. Knee pain follow-up',
                      prefixIcon: Icon(Icons.note),
                      border: OutlineInputBorder(),
                    ),
                    textCapitalization: TextCapitalization.sentences,
                  ),
                  const SizedBox(height: 16),
                  InkWell(
                    onTap: () async {
                      final picked = await showDatePicker(
                        context: sheetContext,
                        initialDate: _selectedDate,
                        firstDate: DateTime.now(),
                        lastDate: DateTime.now().add(
                          const Duration(days: 365),
                        ),
                      );
                      if (picked != null) {
                        setSheetState(() => _selectedDate = picked);
                      }
                    },
                    borderRadius: BorderRadius.circular(12),
                    child: InputDecorator(
                      decoration: const InputDecoration(
                        labelText: 'Appointment Date',
                        prefixIcon: Icon(Icons.event),
                        border: OutlineInputBorder(),
                      ),
                      child: Text(
                        _formatDate(_selectedDate),
                        style: const TextStyle(fontSize: 16),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: () async {
                      final doctor = _doctorController.text.trim();
                      final reason = _reasonController.text.trim();
                      if (doctor.isEmpty || reason.isEmpty) return;

                      Navigator.of(sheetContext).pop();
                      final id = await _viewModel.startNewAppointment(
                        doctorName: doctor,
                        reason: reason,
                        date: _selectedDate,
                      );
                      if (mounted) {
                        context.go('/visit/$id');
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    child: const Text(
                      'Start Preparing',
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
