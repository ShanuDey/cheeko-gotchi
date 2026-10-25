#pragma once
// Face shape model and the table of expressions.
//
// A face is a Shape: a handful of numbers (all in pixels) that the renderer in face.h turns into
// eyes and a mouth. An expression is a named Shape. To add one: write a function below, add it to
// the Expression enum and to looks(), and add the name to the "Face Expression" select in
// cgotchi.yaml (same order as the enum).
//
// display-sim/control.py reads this file to build its tuning sliders. Keep the existing forms:
// Shape fields as "float name = value," declarations, and each expression as
// "inline Shape name() { Shape s; s.field = value; ... return s; }" (or "Shape s = other();").

#include <stddef.h>
#include <stdint.h>

namespace cgotchi {
namespace face {

// Order matches the "Face Expression" select options, so a restored selection stays valid.
enum class Expression : uint8_t { Happy, Sad, Sleepy, Surprised, Angry, Laughing, Confused, Love, Wink, Count };

// Mirrors the voice assistant state kept in cgotchi.yaml (va_state).
enum class Voice : uint8_t { Idle, Listening, Thinking, Replying, Error };

// The defaults are the neutral face: round-cornered eyes and a flat mouth line.
struct Shape {
  float eye_w = 52, eye_h = 58, eye_r = 22;  // eye size and corner radius
  float eye_gap = 92;                        // distance between the eye centers
  float eye_y = 108;                         // eye center height
  float lid_top = 0;                         // height hidden by a flat upper lid (tired)
  float lid_tilt = 0;                        // upper lid slant: + angry (inner corner down), - sad (outer corner down)
  float lid_asym = 0;                        // added to the right eye's tilt, taken from the left's (confused)
  float lid_bot = 0;                         // curved lower lid raised from below (happy squint)
  float wink = 0;                            // height taken off the right eye (wink)
  float look_x = 0, look_y = 0;              // gaze offset
  float mouth_y = 190, mouth_w = 100;        // mouth center height and width
  float mouth_curve = 0;                     // line mouth bend: + smile, - frown
  float mouth_open = 0;                      // opening height, 0 draws a line instead
};

// Every tweened field. Adding a field to Shape means adding it here too.
using Field = float Shape::*;
static const Field kFields[] = {
    &Shape::eye_w,    &Shape::eye_h,    &Shape::eye_r,      &Shape::eye_gap,    &Shape::eye_y,
    &Shape::lid_top,  &Shape::lid_tilt, &Shape::lid_asym,   &Shape::lid_bot,    &Shape::wink,
    &Shape::look_x,   &Shape::look_y,   &Shape::mouth_y,    &Shape::mouth_w,    &Shape::mouth_curve,
    &Shape::mouth_open,
};
constexpr size_t kFieldCount = sizeof(kFields) / sizeof(kFields[0]);
static_assert(kFieldCount * sizeof(float) == sizeof(Shape), "kFields must list every Shape field");

#ifdef CGOTCHI_SIM
// Names for the display simulator's live tuning (settings.txt "shape.<name>"), in kFields order.
static const char *const kFieldNames[] = {
    "eye_w",    "eye_h",    "eye_r",    "eye_gap",  "eye_y",     "lid_top",     "lid_tilt",   "lid_asym",
    "lid_bot",  "wink",     "look_x",   "look_y",   "mouth_y",   "mouth_w",     "mouth_curve", "mouth_open",
};
static_assert(sizeof(kFieldNames) / sizeof(kFieldNames[0]) == kFieldCount, "kFieldNames must match kFields");
#endif

struct Look {
  const char *name;
  Shape shape;
  bool hearts;   // draw hearts instead of eyes
};

// The face before the boot animation opens it: eyes closed, no mouth.
inline Shape asleep_shape() {
  Shape s;
  s.eye_h = 4;
  s.eye_r = 2;
  s.mouth_w = 0;
  return s;
}

// ---- expressions: each one is the neutral Shape plus a few changes --------------------------

inline Shape happy() {
  Shape s;
  s.lid_bot = 14;
  s.mouth_curve = 26;
  return s;
}

inline Shape sad() {
  Shape s;
  s.eye_h = 54;
  s.lid_tilt = -24;
  s.mouth_y = 210;
  s.mouth_w = 90;
  s.mouth_curve = -24;
  return s;
}

inline Shape sleepy() {
  Shape s;
  s.eye_w = 44;
  s.eye_h = 8;
  s.eye_r = 4;
  s.mouth_y = 205;
  s.mouth_w = 18;
  s.mouth_open = 18;
  return s;
}

inline Shape surprised() {
  Shape s;
  s.eye_w = 60;
  s.eye_h = 74;
  s.eye_r = 30;
  s.mouth_y = 205;
  s.mouth_w = 36;
  s.mouth_open = 40;
  return s;
}

inline Shape angry() {
  Shape s;
  s.eye_h = 54;
  s.lid_tilt = 26;
  s.mouth_y = 205;
  s.mouth_w = 80;
  s.mouth_curve = -16;
  return s;
}

inline Shape laughing() {
  Shape s;
  s.eye_h = 50;
  s.lid_bot = 30;
  s.mouth_w = 100;
  s.mouth_open = 34;
  return s;
}

inline Shape confused() {
  Shape s;
  s.lid_tilt = 4;
  s.lid_asym = 14;
  s.look_x = 6;
  s.mouth_w = 60;
  s.mouth_curve = -6;
  return s;
}

inline Shape love() {
  Shape s;
  s.mouth_curve = 22;
  return s;
}

inline Shape wink() {
  Shape s = happy();
  s.wink = 54;
  return s;
}

// Indexed by Expression.
inline const Look *looks() {
  static const Look table[] = {
      {"Happy", happy(), false},     {"Sad", sad(), false},           {"Sleepy", sleepy(), false},
      {"Surprised", surprised(), false}, {"Angry", angry(), false},   {"Laughing", laughing(), false},
      {"Confused", confused(), false},   {"Love", love(), true},      {"Wink", wink(), false},
  };
  return table;
}

}  // namespace face
}  // namespace cgotchi
