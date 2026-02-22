import 'package:go_router/go_router.dart';

import 'package:ag_gimme_gist/views/home_view.dart';
import 'package:ag_gimme_gist/views/ingest_view.dart';
import 'package:ag_gimme_gist/views/prepare_view.dart';
import 'package:ag_gimme_gist/views/recap_view.dart';
import 'package:ag_gimme_gist/views/synthesize_view.dart';
import 'package:ag_gimme_gist/views/visit_detail_view.dart';

final GoRouter appRouter = GoRouter(
  initialLocation: '/',
  routes: <RouteBase>[
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeView(),
    ),
    GoRoute(
      path: '/visit/:id',
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        return VisitDetailView(appointmentId: id);
      },
      routes: <RouteBase>[
        GoRoute(
          path: 'ingest',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return IngestView(appointmentId: id);
          },
        ),
        GoRoute(
          path: 'synthesize',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return SynthesizeView(appointmentId: id);
          },
        ),
        GoRoute(
          path: 'prepare',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return PrepareView(appointmentId: id);
          },
        ),
        GoRoute(
          path: 'recap',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return RecapView(appointmentId: id);
          },
        ),
      ],
    ),
  ],
);
