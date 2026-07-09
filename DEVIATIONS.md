# DEVIATIONS.md — Places Where Implementation Differs from the Original Spec

This document records every intentional deviation from the original specification,
why it was necessary, and how the implementation handles it instead.

---

## 1. `pro_image_editor` API Version & Module Disabling

### What the Spec Said
> "Set `enabled: false` for `paintEditorConfigs`, `textEditorConfigs`, `cropEditorConfigs`, `stickerEditorConfigs`"

### Reality
The `pro_image_editor` v13.2.0 API does **not** have per-editor `enabled` flags.
Instead, the editor tool visibility is controlled by `MainEditorConfigs.tools`,
which takes a `List<SubEditorMode>`.

### What We Did
```dart
MainEditorConfigs(
  tools: const [
    SubEditorMode.filter,
    SubEditorMode.tune,
  ],
)
```
This shows **only** the Filter and Tune tools in the bottom bar. All other
editors (Paint, Text, Crop, Blur, Emoji, Sticker) are omitted from the list
and thus hidden from the user.

### Additional Belt-and-Suspenders
We still pass empty config objects (`const PaintEditorConfigs()` etc.) to
`ProImageEditorConfigs` so that if the library adds fallback behavior,
the defaults are benign.

---

## 2. `customFilterPresets` → `filterList`

### What the Spec Said
> "Inject ... 5 specific premium filters into `filterEditorConfigs.customFilterPresets`"

### Reality
The v13.2.0 API uses `filterList` (type `List<FilterModel>?`), not `customFilterPresets`.

### What We Did
```dart
FilterEditorConfigs(
  filterList: RichyFilters.all,
  ...
)
```
Where `RichyFilters.all` returns a `List<FilterModel>` of 5 entries, each with
a `name` and a `FilterMatrix` (4×5 `List<List<double>>`).

---

## 3. `ColorFilterGenerator` → `FilterModel` + `FilterMatrix`

### What the Spec Said
> "Use `ColorFilterGenerator` with 5x5 matrices"

### Reality
The library defines custom filters through:
- `FilterModel(name: ..., filters: ...)` 
- `FilterMatrix` = `List<List<double>>` (4 rows × 5 columns, RGBA × [multipliers + offset])
- Utility: `ColorFilterAddons` for built-in transformations (brightness, contrast, etc.)

The matrix format is 4×5 (not 5×5) — matching Flutter's `ColorFilter.matrix()` convention:
- Row 0 = Red channel (R_mult, G_mult, B_mult, A_mult, offset)
- Row 1 = Green channel
- Row 2 = Blue channel
- Row 3 = Alpha channel

### What We Did
We define 5 `FilterModel` constants in `lib/editor/custom_filters.dart` using
4×5 matrices with carefully tuned values for:
1. **Peach** — warm rosy skin tones
2. **Mute Peach** — matte/faded peach with lifted blacks
3. **Milk+** — high-key cream, increased exposure
4. **Butter** — vintage warm amber
5. **Cool** — boosted blue, protected reds

---

## 4. Tune Editor Labels — No `tr()` Wrapper

### What the Spec Said
> "Wrap all strings using `easy_localization` format (e.g., `tr('key')`)"

### Reality
`TuneAdjustmentItem.label` is used at config-construction time (not widget build time),
so `tr()` cannot be used because it requires a `BuildContext`.

### What We Did
Tune adjustment labels use plain English strings (`'Brightness'`, `'Contrast'`,
`'Saturation'`). The library's built-in i18n handles translation of these if
configured. All custom UI strings (home screen, error messages, etc.) use the
proper `'key'.tr()` extension method.

---

## 5. `ProImageEditor` Constructor

### What the Spec Said
> "automatically pass the image file to the customized `ProImageEditor` view"

### What We Did
We use `ProImageEditor.file(imageFile, ...)` which accepts a `File` object.
The `image_picker` returns `XFile`, which we convert via `File(xfile.path)`.

---

## 6. Share Service — `share_plus` API

### What the Spec Said
> "Promptly trigger `share_plus` to launch the native iOS/Android Share Sheet"

### Reality
`share_plus` v13.2.0 uses `SharePlus.instance.share(ShareParams(...))` API
instead of the older `Share.shareXFiles(...)` or `Share.share(...)`.

### What We Did
```dart
await SharePlus.instance.share(
  ShareParams(
    files: [XFile(file.path)],
    subject: 'RICHY Lite',
  ),
);
```

---

## 7. Platform Manifest Files — Template Status

### What We Did
The `AndroidManifest.xml` and `Info.plist` provided are **reference templates**.
They contain the correct permission declarations but the actual Flutter project
must be created with `flutter create --platforms=android,ios .` first, which
generates the full native project structure.

The build scripts handle this:
- **Android**: `flutter create` generates the Gradle wrapper, build files, etc.
- **iOS**: `flutter create` generates the Xcode project; Podfile is generated on build.

---

## 8. Error Logger Path

### What We Did
The error logger writes to the app's documents directory via `path_provider`.
The build scripts also write build logs to `error_logs/` at the project root.
These are separate log streams:
- **App runtime logs**: `<app_documents>/error_logs/richy_errors.log`
- **Build logs**: `<project_root>/error_logs/build_android_*.log`

---

## Summary Table

| Spec Reference | Spec Expectation | Actual Implementation |
|---------------|-----------------|----------------------|
| `enabled: false` per editor | Per-editor boolean toggle | `MainEditorConfigs.tools` list — only include filter + tune |
| `customFilterPresets` | Property name | `filterList` (v13.2.0 API) |
| `ColorFilterGenerator` | Class name | `FilterModel(name, filters: FilterMatrix)` |
| 5×5 matrices | Matrix dimensions | 4×5 matrices (Flutter convention) |
| `tr('key')` for all strings | Wrap all strings | Only custom UI strings; tune labels use plain English |
| `share_plus` API | Generic trigger | `SharePlus.instance.share(ShareParams(...))` |
| `easy_localization` v3 | `tr()` global function | `'key'.tr()` extension method (v3.x idiom) |

---

*Last updated: 2026-07-09*
*For questions, refer to the source code comments in each file.*
