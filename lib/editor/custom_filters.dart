import 'package:pro_image_editor/pro_image_editor.dart';

/// Five premium custom color filter presets for RICHY Lite.
///
/// Each filter uses a 4×5 color matrix that maps normalized
/// [R, G, B, A, 1] input to [R', G', B', A'] output via:
///
///   R' = m[0][0]*R + m[0][1]*G + m[0][2]*B + m[0][3]*A + m[0][4]
///   G' = m[1][0]*R + m[1][1]*G + m[1][2]*B + m[1][3]*A + m[1][4]
///   B' = m[2][0]*R + m[2][1]*G + m[2][2]*B + m[2][3]*A + m[2][4]
///   A' = m[3][0]*R + m[3][1]*G + m[3][2]*B + m[3][3]*A + m[3][4]
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
  //    High red/orange luminance, slight fade in shadows.
  // ────────────────────────────────────────────────────────────────
  static const FilterModel peach = FilterModel(
    name: 'Peach 🍑',
    filters: [
      [1.08, 0.06, -0.03, 0.0, 0.02], // R: warm boost
      [0.02, 1.04, 0.01, 0.0, 0.02], // G: subtle warmth
      [-0.04, 0.0, 0.92, 0.0, 0.01], // B: slight reduction
      [0.00, 0.0, 0.00, 1.0, 0.00], // A: unchanged
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 2. Mute Peach 🌸 — Matte/faded peach tone
  //    Lower overall saturation, lifted black points.
  // ────────────────────────────────────────────────────────────────
  static const FilterModel mutePeach = FilterModel(
    name: 'Mute Peach 🌸',
    filters: [
      [0.35, 0.35, 0.15, 0.0, 0.05], // R: desaturated + peach
      [0.25, 0.35, 0.15, 0.0, 0.06], // G: desaturated
      [0.12, 0.18, 0.28, 0.0, 0.09], // B: lifted blacks
      [0.00, 0.00, 0.00, 1.0, 0.00], // A: unchanged
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 3. Milk+ 🥛 — Bright, dreamlike high-key cream
  //    Increased exposure, subtle soft-white tint mixing.
  // ────────────────────────────────────────────────────────────────
  static const FilterModel milkPlus = FilterModel(
    name: 'Milk+ 🥛',
    filters: [
      [1.12, 0.05, 0.02, 0.0, 0.10], // R: brightened + warm
      [0.04, 1.10, 0.04, 0.0, 0.10], // G: brightened
      [0.02, 0.05, 1.08, 0.0, 0.12], // B: brightened, slight lift
      [0.00, 0.00, 0.00, 1.0, 0.00], // A: unchanged
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 4. Butter 🧈 — Vintage warm retro feel
  //    Shift white balance to warm yellow (+Kelvin), amber highlights.
  // ────────────────────────────────────────────────────────────────
  static const FilterModel butter = FilterModel(
    name: 'Butter 🧈',
    filters: [
      [1.12, 0.12, -0.06, 0.0, 0.03], // R: warm amber boost
      [0.08, 1.08, 0.06, 0.0, 0.04], // G: warm yellow-green
      [-0.06, 0.06, 0.90, 0.0, 0.02], // B: suppressed, warm
      [0.00, 0.00, 0.00, 1.0, 0.00], // A: unchanged
    ],
  );

  // ────────────────────────────────────────────────────────────────
  // 5. Cool ❄️ — Clean, high-contrast translucent
  //    Boost blue channel, suppress greens, protect red/magenta.
  // ────────────────────────────────────────────────────────────────
  static const FilterModel cool = FilterModel(
    name: 'Cool ❄️',
    filters: [
      [1.06, -0.04, 0.05, 0.0, -0.02], // R: protect red/magenta
      [-0.02, 0.94, 0.06, 0.0, -0.01], // G: slight suppress
      [0.00, -0.06, 1.18, 0.0, 0.04], // B: boosted blue
      [0.00, 0.00, 0.00, 1.0, 0.00], // A: unchanged
    ],
  );
}
