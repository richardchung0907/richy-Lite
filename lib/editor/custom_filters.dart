import 'package:pro_image_editor/pro_image_editor.dart';

/// Five premium custom color filter presets for RICHY Lite.
///
/// Each filter uses a 4x5 color matrix, stored as a flat 20-element
/// `List<double>` matching Flutter's `ColorFilter.matrix()` convention.
///
/// Matrix layout (row-major, 20 values):
///   [Rr, Rg, Rb, Ra, Ro, Gr, Gg, Gb, Ga, Go, Br, Bg, Bb, Ba, Bo, Ar, Ag, Ab, Aa, Ao]
///
/// All values are in [0, 1] normalized space.
class RichyFilters {
  RichyFilters._();

  /// Returns the complete list of 5 custom filter presets.
  static List<FilterModel> get all => [
        peach,
        mutePeach,
        milkPlus,
        butter,
        cool,
      ];

  // ────────────────────────────────────────────────────────────────
  // 1. Peach 🍑 — Warm rosy skin tones
  // ────────────────────────────────────────────────────────────────
  static const FilterModel peach = FilterModel(
    name: 'Peach 🍑',
    filters: [
      [1.08, 0.06, -0.03, 0.0, 0.02, 0.02, 1.04, 0.01, 0.0, 0.02, -0.04, 0.0, 0.92, 0.0, 0.01, 0.00, 0.0, 0.00, 1.0, 0.00],
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 2. Mute Peach 🌸 — Matte/faded peach tone
  // ────────────────────────────────────────────────────────────────
  static const FilterModel mutePeach = FilterModel(
    name: 'Mute Peach 🌸',
    filters: [
      [0.35, 0.35, 0.15, 0.0, 0.05, 0.25, 0.35, 0.15, 0.0, 0.06, 0.12, 0.18, 0.28, 0.0, 0.09, 0.00, 0.00, 0.00, 1.0, 0.00],
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 3. Milk+ 🥛 — Bright, dreamlike high-key cream
  // ────────────────────────────────────────────────────────────────
  static const FilterModel milkPlus = FilterModel(
    name: 'Milk+ 🥛',
    filters: [
      [1.12, 0.05, 0.02, 0.0, 0.10, 0.04, 1.10, 0.04, 0.0, 0.10, 0.02, 0.05, 1.08, 0.0, 0.12, 0.00, 0.00, 0.00, 1.0, 0.00],
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 4. Butter 🧈 — Vintage warm retro feel
  // ────────────────────────────────────────────────────────────────
  static const FilterModel butter = FilterModel(
    name: 'Butter 🧈',
    filters: [
      [1.12, 0.12, -0.06, 0.0, 0.03, 0.08, 1.08, 0.06, 0.0, 0.04, -0.06, 0.06, 0.90, 0.0, 0.02, 0.00, 0.00, 0.00, 1.0, 0.00],
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 5. Cool ❄️ — Clean, high-contrast translucent
  // ────────────────────────────────────────────────────────────────
  static const FilterModel cool = FilterModel(
    name: 'Cool ❄️',
    filters: [
      [1.06, -0.04, 0.05, 0.0, -0.02, -0.02, 0.94, 0.06, 0.0, -0.01, 0.00, -0.06, 1.18, 0.0, 0.04, 0.00, 0.00, 0.00, 1.0, 0.00],
    ],
  );
}
