import 'package:flutter/material.dart';
import 'package:ag_gimme_gist/services/med_gemma_service.dart';
import 'package:ag_gimme_gist/services/symptom_logger_service.dart';

class RecapViewModel extends ChangeNotifier {
  final SymptomLoggerService _audioService = SymptomLoggerService();
  final MedGemmaService _aiService = MedGemmaService();

  bool _isRecording = false;
  bool get isRecording => _isRecording;

  bool _isProcessing = false;
  bool get isProcessing => _isProcessing;

  VisitRecap? _recap;
  VisitRecap? get recap => _recap;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  Future<void> stopRecordingAndProcess({required bool isMocked}) async {
    _isRecording = false;
    _isProcessing = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // Typically we'd save the recording path and process it
      final audioPath = await _audioService.recordAudio(isMocked: isMocked);
      final transcription = await _audioService.transcribeAudio(audioPath, isMocked: isMocked);
      _recap = await _aiService.generateRecap(transcription: transcription, isMocked: isMocked);
    } catch (e) {
      _errorMessage = 'Failed to process visit audio: \$e';
    } finally {
      _isProcessing = false;
      notifyListeners();
    }
  }

  void startRecording() {
    _isRecording = true;
    _recap = null;
    notifyListeners();
  }
}
