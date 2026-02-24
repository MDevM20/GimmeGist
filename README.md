<p align="center">
  <img src="docs/logo_only.png" alt="GimmeGist Logo" width="200" />
</p>

# GimmeGist

[![Android CI](https://github.com/MDevM20/GimmeGist/actions/workflows/android_build.yml/badge.svg)](https://github.com/MDevM20/GimmeGist/actions/workflows/android_build.yml)

**AI-powered prep for smarter doctor visits.**

GimmeGist is a MedGemma-powered intelligence platform designed to maximize the value of the "Clinical Hour." By synthesizing wearable data from Google Health Connect and translating complex clinical images and reports into patient-accessible language, GimmeGist closes the communication gap between patients and providers.

Built on the HAI-DEF MedGemma models, the platform identifies physiological anomalies, demystifies medical jargon, and generates strategic consultation agendas. GimmeGist transforms passive data into "The Gist"—empowering patients to arrive prepared and enabling doctors to focus on high-level diagnostic reasoning.

## Core Features (4 Phases)

1. **Ingest**: Seamlessly sync wearable data (Heart Rate, Steps) via Health Connect and upload diagnostic PDFs or medical images. All ingested data and appointment contexts are persisted securely throughout your session.
2. **Synthesize**: MedGemma processes the inputs to generate a 1-page "Gist" summary (Cause, Location, Goal) and an "Anomaly Alert" log based on biometric outliers.
3. **Prepare**: A Strategic Consultation Agenda is generated, featuring high-yield questions prioritized for a standard 15-minute visit. AI Insights surface gentle exploratory questions based on secondary diagnostic safety nets.
4. **Recap**: Post-visit, the app processes authorized consultation audio to provide a plain-language summary of the doctor's instructions, action items, and follow-ups.

## AI Models (`ai_models/`)

GimmeGist's intelligence layer is powered by three **LangGraph + MedGemma 27B** models, each logged and tracked via **MLflow**. All models follow a shared pipeline pattern: `ingest → split → features → model → evaluate`, orchestrated by `run_pipeline.py`.

### 1. [Clinical Translation](ai_models/clinical_translation/README.md)

Translates complex clinical and specialty medical reports into accessible, patient-friendly summaries. A 3-node LangGraph (`extract_cause → extract_location → extract_treatment`) decomposes clinical text into three plain-language dimensions: *what* is happening, *where* in the body, and *how* it's typically treated.

- **Foundation Model:** MedGemma 27B (text-only)
- **Evaluation:** DeepEval faithfulness scoring + readability metrics (Flesch RE ≥ 60, FK Grade ≤ 8)
- **Dataset:** MedLane — 12,801+ clinical ↔ simplified sentence pairs

### 2. [Question Generation](ai_models/question_generation/README.md)

Generates strategic patient questions from medical reports, health data, and symptoms to maximize the value of a 15-minute consultation. A 3-node LangGraph (`generate_understanding → generate_treatment → generate_lifestyle`) produces prioritized questions across three categories.

- **Foundation Model:** MedGemma 27B (text-only)
- **Evaluation:** DeepEval faithfulness scoring (combined + per-category)
- **Dataset:** MedQuAD — 47,000+ medical Q&A pairs from 12 NIH websites

### 3. [Secondary Oversight](ai_models/secondary_oversight/README.md)

Acts as a secondary diagnostic safety net by parsing radiology images alongside diagnostic text to identify potential unaddressed findings. Instead of surfacing raw clinical flags, the model generates **gentle, exploratory patient questions** to add to the consultation agenda.

- **Foundation Model:** MedGemma 27B (**multimodal** — images + text)
- **Evaluation:** Finding capture rate (DeepEval GEval ≥ 0.6) + tone quality (non-alarmist scoring, readability)
- **Dataset:** ReXErr-v1 (26K+ chest X-ray reports with injected errors) + built-in synthetic demo set

## Architecture & Tech Stack

- **Framework**: Flutter (targeting Android primarily, requires `minSdkVersion 26`).
- **Design System**: Material 3, Google Fonts (Outfit), subtle Noise Background, customized cards with elevated shadows. Full branding with custom app icons.
- **Navigation**: `go_router` for structured routing, deeply integrating `PopScope` for seamless Android back-gesture support across multi-step visit flows.
- **State Management**: Strict native MVVM (Model-View-ViewModel) using `ChangeNotifier` and `ValueNotifier` (No Riverpod, Bloc, or GetX). Includes robust data persistence across view navigations.
- **CI/CD**: Fully automated GitHub Actions workflow for building Android APKs.
- **Services (Mocked for initial MVP)**: 
  - `MedGemmaService` for AI text and multimodal generation.
  - `HealthConnectService` for wearable data aggregation.
  - `SymptomLoggerService` for audio recording and transcription.

## Getting Started

### Prerequisites
- Flutter SDK (latest stable)
- Android Studio / Android SDK (for Android deployment)
- A physical Android device (for Health Connect and audio features) or an Emulator.

### Installation

1. Clone or initialize the repository.
2. Fetch dependencies:
   ```bash
   flutter pub get
   ```
3. Run the application:
   ```bash
   flutter run
   ```

### Running on a Physical Android Device (ADB)

If your device is plugged in and ADB is authorized (USB Debugging enabled):

1. Check that Flutter recognizes your device:
   ```bash
   flutter devices
   ```
2. Run the app specifying the device ID (if multiple devices/emulators are connected):
   ```bash
   flutter run -d <your-device-id>
   ```
   *Note: If only one device is connected, `flutter run` will automatically launch on it.*

## Development Modes

The app includes a built-in **Mock Toggle** accessible from the `IngestView`'s top App Bar. 
- **Mock Mode (Orange Bug Icon)**: Simulates AI delays and returns pre-populated mock data for testing UI flows without incurring API costs.
- **Real Mode (Green Cloud Icon)**: Attempts to connect to real endpoints (requires further Google Cloud / Vertex AI and Firebase setup).
