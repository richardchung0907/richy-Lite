import 'package:pro_image_editor/pro_image_editor.dart';

/// Five premium custom color filter presets for RICHY Lite.
///
/// Each filter uses a 4x5 color matrix, stored as a flat 20-element
/// `List<double>` matching Flutter's `ColorFilter.matrix()` convention.
///
/// Matrix layout (row-major, 20 values):
///   [Rr, Rg, Rb, Ra, Ro, Gr, Gg, Gb, Ga, Go, Br, Bg, Bb, Ba, Bo, Ar, Ag, Ab, Aa, Ao]
///
/// All multiplier values are in [0, 1] normalized space, 
/// but translation values (offsets) must be in [0, 255] space for Flutter.
class RichyFilters {
  RichyFilters._();

  /// Returns the complete list of 5 custom filter presets.
  static List<FilterModel> get all => [
        vanillaCloud,
        morningDew,
        snowyWhisper,
        sunsetLatte,
        peachSorbet,
      ];

  // ────────────────────────────────────────────────────────────────
  // 1. Vanilla Cloud ☁️ — Warm rosy skin tones
  // ────────────────────────────────────────────────────────────────
  static const FilterModel vanillaCloud = FilterModel(
    name: 'Vanilla Cloud ☁️',
    filters: [
      [
        0.5639, 0.0000, 0.0000, 0.0000, 123.1757,
        0.0000, 0.7290, 0.0000, 0.0000, 103.3817,
        0.0000, 0.0000, 0.8628, 0.0000, 103.8050,
        0.0000, 0.0000, 0.0000, 1.0000, 0.0000,
      ],
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 2. Morning Dew 💧 — Matte/faded peach tone
  // ────────────────────────────────────────────────────────────────
  static const FilterModel morningDew = FilterModel(
    name: 'Morning Dew 💧',
    filters: [
      [
        1.1503, 0.0000, 0.0000, 0.0000, -12.0910,
        0.0000, 1.2162, 0.0000, 0.0000, -20.1258,
        0.0000, 0.0000, 1.2202, 0.0000, -4.2369,
        0.0000, 0.0000, 0.0000, 1.0000, 0.0000,
      ],
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 3. Snowy Whisper 🌨️ — Bright, dreamlike high-key cream
  // ────────────────────────────────────────────────────────────────
  static const FilterModel snowyWhisper = FilterModel(
    name: 'Snowy Whisper 🌨️',
    filters: [
      [
        0.7520, 0.0000, 0.0000, 0.0000, 90.0334,
        0.0000, 0.7737, 0.0000, 0.0000, 89.8946,
        0.0000, 0.0000, 0.7951, 0.0000, 92.2068,
        0.0000, 0.0000, 0.0000, 1.0000, 0.0000,
      ],
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 4. Sunset Latte ☕ — Vintage warm retro feel
  // ────────────────────────────────────────────────────────────────
  static const FilterModel sunsetLatte = FilterModel(
    name: 'Sunset Latte ☕',
    filters: [
      [
        1.0571, 0.0000, 0.0000, 0.0000, -4.8840,
        0.0000, 1.3677, 0.0000, 0.0000, -89.4604,
        0.0000, 0.0000, 1.0750, 0.0000, -50.8678,
        0.0000, 0.0000, 0.0000, 1.0000, 0.0000,
      ],
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 5. Peach Sorbet 🍧 — Clean, high-contrast translucent
  // ────────────────────────────────────────────────────────────────
  static const FilterModel peachSorbet = FilterModel(
    name: 'Peach Sorbet 🍧',
    filters: [
      [
        1.0025, 0.0000, 0.0000, 0.0000, 15.7595,
        0.0000, 0.9344, 0.0000, 0.0000, 12.8329,
        0.0000, 0.0000, 0.9278, 0.0000, 19.6865,
        0.0000, 0.0000, 0.0000, 1.0000, 0.0000,
      ],
    ],
  );
}
