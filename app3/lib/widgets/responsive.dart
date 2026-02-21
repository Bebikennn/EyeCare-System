import 'package:flutter/material.dart';

/// Lightweight responsive helpers for phone/tablet/desktop layouts.
///
/// Design goals:
/// - Keep existing UI/UX, just make it adapt and avoid overflow.
/// - Center content on wide screens with a max width.
/// - Use consistent, responsive page padding.

enum ResponsiveBreakpoint { compact, medium, expanded }

ResponsiveBreakpoint breakpointForWidth(double width) {
  if (width < 600) return ResponsiveBreakpoint.compact;
  if (width < 1024) return ResponsiveBreakpoint.medium;
  return ResponsiveBreakpoint.expanded;
}

EdgeInsets responsivePagePadding(double width) {
  final bp = breakpointForWidth(width);
  switch (bp) {
    case ResponsiveBreakpoint.compact:
      return const EdgeInsets.symmetric(horizontal: 16, vertical: 16);
    case ResponsiveBreakpoint.medium:
      return const EdgeInsets.symmetric(horizontal: 24, vertical: 20);
    case ResponsiveBreakpoint.expanded:
      return const EdgeInsets.symmetric(horizontal: 32, vertical: 24);
  }
}

/// Constrains [child] to [maxWidth] and centers it on wide screens.
class ResponsiveConstrained extends StatelessWidget {
  final Widget child;
  final double maxWidth;
  final Alignment alignment;
  final EdgeInsetsGeometry? padding;

  const ResponsiveConstrained({
    super.key,
    required this.child,
    required this.maxWidth,
    this.alignment = Alignment.topCenter,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final defaultPadding = responsivePagePadding(constraints.maxWidth);
        return Align(
          alignment: alignment,
          child: Padding(
            padding: padding ?? defaultPadding,
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: maxWidth),
              child: child,
            ),
          ),
        );
      },
    );
  }
}

/// A scrollable, centered, width-constrained page body.
class ResponsiveScroll extends StatelessWidget {
  final Widget child;
  final double maxWidth;
  final Alignment alignment;
  final EdgeInsetsGeometry? padding;

  const ResponsiveScroll({
    super.key,
    required this.child,
    required this.maxWidth,
    this.alignment = Alignment.topCenter,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final defaultPadding = responsivePagePadding(constraints.maxWidth);
        return SingleChildScrollView(
          child: ResponsiveConstrained(
            maxWidth: maxWidth,
            alignment: alignment,
            padding: padding ?? defaultPadding,
            child: child,
          ),
        );
      },
    );
  }
}
