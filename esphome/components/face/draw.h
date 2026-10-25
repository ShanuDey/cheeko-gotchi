#pragma once
// Face renderer: turns one Frame into drawing calls. Pure drawing, no state and no timing, so it
// also runs on a PC (tools/face_preview). `It` is the ESPHome display (or a test canvas) and
// `Color` its color type.

#include <math.h>
#include <stdint.h>

#include "looks.h"

namespace cgotchi {
namespace face {

constexpr int kCenterX = 120;   // the panel is 240 px wide

// Everything needed to draw one frame: the animated shape plus the effects drawn over it.
struct Frame {
  Shape shape;
  float blink = 0;       // 0 open .. 1 shut
  bool hearts = false;   // hearts instead of eyes
  float heart_size = 56;
  int ring = -1;         // >= 0: attention rings around the eyes, this many px wider than the eye
  int dots = -1;         // >= 0: three "thinking" dots instead of a mouth, this one lit
};

namespace detail {

template <typename It, typename Color>
void round_rect(It &it, int x, int y, int w, int h, int r, Color c) {
  if (w < 1 || h < 1) return;
  if (r > w / 2) r = w / 2;
  if (r > h / 2) r = h / 2;
  it.filled_rectangle(x + r, y, w - 2 * r, h, c);
  it.filled_rectangle(x, y + r, w, h - 2 * r, c);
  it.filled_circle(x + r, y + r, r, c);
  it.filled_circle(x + w - 1 - r, y + r, r, c);
  it.filled_circle(x + r, y + h - 1 - r, r, c);
  it.filled_circle(x + w - 1 - r, y + h - 1 - r, r, c);
}

// side: -1 left eye, +1 right eye. open: 1 fully open .. 0 shut, shrinks the eye and its lids
// together (blink, wink). The lids are drawn in the background color over the eye.
template <typename It, typename Color>
void eye(It &it, int cx, int cy, const Shape &s, float open, float tilt, int side, Color fg, Color bg) {
  const int w = (int) s.eye_w, hh = (int) fmaxf(4.0f, s.eye_h * open);
  const int x0 = cx - w / 2, y0 = cy - hh / 2, x1 = x0 + w - 1, y1 = y0 + hh - 1;
  const float lid_top = s.lid_top * open, lid_bot = s.lid_bot * open;
  tilt *= open;
  round_rect(it, x0, y0, w, hh, (int) s.eye_r, fg);

  if (lid_top >= 1) it.filled_rectangle(x0 - 1, y0 - 1, w + 2, (int) lid_top + 1, bg);
  if (fabsf(tilt) >= 1) {
    // The lid is a triangle across the top whose third corner dips by |tilt|. Angry dips the
    // corner next to the nose, sad the corner away from it.
    const int inner = side < 0 ? x1 : x0, outer = side < 0 ? x0 : x1;
    const int dip_x = tilt > 0 ? inner : outer;   // which top corner the lid dips towards
    it.filled_triangle(x0 - 1, y0 - 1, x1 + 1, y0 - 1, dip_x, y0 + (int) fabsf(tilt), bg);
  }
  if (lid_bot >= 1) {
    // A large background circle rising from below: a curved lower lid (cheek).
    const int r = (int) (s.eye_w * 0.8f);
    it.filled_circle(cx, y1 + r - (int) lid_bot, r, bg);
  }
}

template <typename It, typename Color>
void heart(It &it, int cx, int cy, float size, Color c) {
  const int r = (int) (size * 0.27f), dx = (int) (size * 0.24f), top = cy - (int) (size * 0.12f);
  it.filled_circle(cx - dx, top, r, c);
  it.filled_circle(cx + dx, top, r, c);
  it.filled_triangle(cx - (int) (size * 0.5f), top + 3, cx + (int) (size * 0.5f), top + 3, cx, cy + (int) (size * 0.48f), c);
}

// Bent mouth line, 4 px thick. amp > 0 bends the middle down (smile), amp < 0 up (frown).
template <typename It, typename Color>
void mouth_line(It &it, int cx, int y, int w, float amp, Color c) {
  constexpr int kSegments = 16;
  int px = cx - w / 2, py = y + 0;
  for (int i = 1; i <= kSegments; i++) {
    const float t = i / (float) kSegments;
    const int x = cx - w / 2 + (int) (w * t);
    const int yy = y + (int) (amp * sinf(t * 3.14159265f));
    for (int k = 0; k < 4; k++) it.line(px, py + k, x, yy + k, c);
    px = x;
    py = yy;
  }
}

}  // namespace detail

template <typename It, typename Color>
void draw(It &it, const Frame &f, Color fg, Color bg) {
  const Shape &s = f.shape;
  const int ey = (int) (s.eye_y + s.look_y);
  const int lx = kCenterX - (int) (s.eye_gap / 2) + (int) s.look_x;
  const int rx = kCenterX + (int) (s.eye_gap / 2) + (int) s.look_x;

  if (f.hearts) {
    detail::heart(it, lx, ey, f.heart_size, fg);
    detail::heart(it, rx, ey, f.heart_size, fg);
  } else {
    const float open = 1 - f.blink;
    const float right_open = open * fmaxf(0.0f, 1 - s.wink / s.eye_h);
    detail::eye(it, lx, ey, s, open, s.lid_tilt - s.lid_asym, -1, fg, bg);
    detail::eye(it, rx, ey, s, right_open, s.lid_tilt + s.lid_asym, +1, fg, bg);
    if (f.ring >= 0) {
      const int r = (int) (s.eye_h / 2) + f.ring + 6;
      it.circle(lx, ey, r, fg);
      it.circle(rx, ey, r, fg);
    }
  }

  const int my = (int) s.mouth_y;
  if (f.dots >= 0) {
    for (int d = 0; d < 3; d++) it.filled_circle(kCenterX - 28 + d * 28, my, d == f.dots ? 9 : 5, fg);
  } else if (s.mouth_w >= 2) {
    if (s.mouth_open >= 2) {
      const int w = (int) s.mouth_w, h = (int) s.mouth_open;
      detail::round_rect(it, kCenterX - w / 2, my - h / 2, w, h, h / 2, fg);
    } else {
      detail::mouth_line(it, kCenterX, my, (int) s.mouth_w, s.mouth_curve, fg);
    }
  }
}

}  // namespace face
}  // namespace cgotchi
