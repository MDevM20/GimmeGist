import 'package:flutter/material.dart';
import 'package:ag_gimme_gist/services/med_gemma_service.dart';

class SynthesizeViewModel extends ChangeNotifier {
  final MedGemmaService _aiService = MedGemmaService();

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  GistSummary? _summary;
  GistSummary? get summary => _summary;

  List<AnomalyAlert> _anomalies = [];
  List<AnomalyAlert> get anomalies => _anomalies;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  Future<void> evaluateData({required bool isMocked}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // In a real app, we'd pass the actual text from the PDF and the HealthConnect data.
      _summary = await _aiService.generateGist(input: 'Medial meniscal degeneration...', isMocked: isMocked);
      _anomalies = await _aiService.detectAnomalies(healthData: [], isMocked: isMocked);
    } catch (e) {
      _errorMessage = 'Failed to generate gist: \$e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
