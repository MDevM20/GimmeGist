import 'dart:math';
import 'package:flutter/material.dart';

class NoiseBackground extends StatelessWidget {
  final Widget child;
  
  const NoiseBackground({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Base color or gradient could go here based on theme
        Container(
          color: Theme.of(context).colorScheme.surface,
        ),
        // Noise overlay
        Positioned.fill(
          child: IgnorePointer(
            child: Opacity(
              opacity: 0.03, // Very subtle
              child: CustomPaint(
                painter: _NoisePainter(),
              ),
            ),
          ),
        ),
        // Main content
        Positioned.fill(child: child),
      ],
    );
  }
}

class _NoisePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final random = Random(42); // specific seed for consistent look
    final paint = Paint()
      ..color = Colors.black
      ..strokeWidth = 1.0;

    // Draw random points to simulate grain/noise
    // We sample a grid to avoid completely filling the canvas with slow drawing
    const double step = 3.0;
    for (double x = 0; x < size.width; x += step) {
      for (double y = 0; y < size.height; y += step) {
        if (random.nextDouble() > 0.5) {
          canvas.drawRect(Rect.fromLTWH(x, y, 1, 1), paint);
        }
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
