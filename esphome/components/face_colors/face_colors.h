#pragma once
// Face color presets shared by the "Face Color Preset" select and the "Face Color" light.
// Keep the names in sync with the select options in cgotchi.yaml.
struct FacePreset {
  const char *name;
  float r, g, b;
};

static const FacePreset FACE_PRESETS[] = {
    {"Blue", 0.0f, 0.78f, 1.0f},   {"Green", 0.2f, 1.0f, 0.3f},  {"Pink", 1.0f, 0.4f, 0.7f},
    {"Orange", 1.0f, 0.55f, 0.0f}, {"Purple", 0.65f, 0.3f, 1.0f}, {"Red", 1.0f, 0.2f, 0.2f},
    {"Yellow", 1.0f, 0.9f, 0.1f},  {"White", 1.0f, 1.0f, 1.0f},
};
