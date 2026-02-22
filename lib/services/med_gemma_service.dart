
class GistSummary {
  final String cause;
  final String location;
  final String goal;

  GistSummary({
    required this.cause,
    required this.location,
    required this.goal,
  });
}

class AnomalyAlert {
  final String title;
  final String description;
  final String timestamp;
  final bool isHighPriority;

  AnomalyAlert({
    required this.title,
    required this.description,
    required this.timestamp,
    required this.isHighPriority,
  });
}

class VisitRecap {
  final String summary;
  final List<String> actionItems;
  final List<String> followUps;

  VisitRecap({
    required this.summary,
    required this.actionItems,
    required this.followUps,
  });
}

class StrategicQuestion {
  final String category;
  final String question;
  final bool isSecondaryOversight;

  StrategicQuestion({
    required this.category,
    required this.question,
    this.isSecondaryOversight = false,
  });
}

class MedGemmaService {
  Future<GistSummary> generateGist({required String input, required bool isMocked}) async {
    if (isMocked) {
      await Future.delayed(const Duration(seconds: 2));
      return GistSummary(
        cause: 'The cushion in your knee is showing age-related wear and has developed a small split.',
        location: 'This is on the inner side of your knee, a common area for these issues.',
        goal: 'Treatment usually focuses on reducing swelling and strengthening surrounding muscles rather than immediate surgery.',
      );
    }
    
    // Real implementation would call Vertex AI MedGemma endpoint here
    throw UnimplementedError('Real MedGemma API call not yet implemented.');
  }

  Future<List<AnomalyAlert>> detectAnomalies({
    required List<dynamic> healthData, 
    required bool isMocked
  }) async {
    if (isMocked) {
      await Future.delayed(const Duration(milliseconds: 500));
      return [
        AnomalyAlert(
          title: 'Sustained Heart Rate Spike',
          description: 'Your heart rate reached 115 bpm while resting. This is unusually high for your baseline.',
          timestamp: '1 hour ago',
          isHighPriority: true,
        ),
      ];
    }

    throw UnimplementedError('Real anomaly detection not yet implemented.');
  }

  Future<List<StrategicQuestion>> generateQuestions({required bool isMocked}) async {
    if (isMocked) {
      await Future.delayed(const Duration(seconds: 1));
      return [
        StrategicQuestion(
          category: 'Understanding',
          question: "Does the 'wear and tear' mean my knee is aging faster than normal, and what can I do to protect it?",
        ),
        StrategicQuestion(
          category: 'Treatment',
          question: 'Can we try physical therapy first, and which muscles should I focus on to support the joint?',
        ),
        StrategicQuestion(
          category: 'Lifestyle',
          question: 'Are there specific movements, like squatting, that I should avoid right now?',
        ),
        StrategicQuestion(
          category: 'Exploratory',
          question: 'Doctor, are there any early signs of osteoporosis on the imaging that we should monitor?',
          isSecondaryOversight: true,
        ),
      ];
    }
    throw UnimplementedError('Real question generation not yet implemented.');
  }

  Future<VisitRecap> generateRecap({required String transcription, required bool isMocked}) async {
    if (isMocked) {
      await Future.delayed(const Duration(seconds: 2));
      return VisitRecap(
        summary: 'The doctor confirmed that your meniscus tear is mild and does not require surgery at this time. The focus will be on conservative management.',
        actionItems: [
          'Start physical therapy (2x/week) for quad/hamstring strengthening.',
          'Avoid deep squatting for the next 4 weeks.',
        ],
        followUps: [
          'Follow-up appointment in 1 month to re-evaluate the knee.',
          'Schedule a DEXA scan to check bone density based on imaging findings.',
        ],
      );
    }
    
    throw UnimplementedError('Real recap generation not yet implemented.');
  }
}


