import 'package:flutter/material.dart';
import 'package:ag_gimme_gist/services/med_gemma_service.dart';

class PrepareViewModel extends ChangeNotifier {
  final MedGemmaService _aiService = MedGemmaService();

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  List<StrategicQuestion> _questions = [];
  List<StrategicQuestion> get questions => _questions;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  Future<void> loadQuestions({required bool isMocked}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _questions = await _aiService.generateQuestions(isMocked: isMocked);
    } catch (e) {
      _errorMessage = 'Failed to load questions: \$e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
