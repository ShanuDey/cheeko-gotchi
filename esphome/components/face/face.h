#pragma once
// Face animation: eases the shown Shape towards the wanted expression and adds the idle life
// (blinking, wandering gaze) and the voice assistant effects. Drawing itself is in draw.h.
//
// Use from the display lambda, once per redraw:
//     auto &f = cgotchi::face::instance();
//     f.update({expression, voice, speaking, booting}, millis());
//     f.draw(it, color, background);
// and from a short interval, to run frames only while something moves:
//     if (f.visible && f.needs_frame(millis())) id(lcd).update();

#include <math.h>
#include <stdint.h>

#include "colors.h"
#include "draw.h"
#include "looks.h"

namespace cgotchi {
namespace face {

// What the face should show right now. Built from the entities in cgotchi.yaml.
struct Input {
  Expression expression = Expression::Happy;
  Voice voice = Voice::Idle;
  bool speaking = false;   // audio is playing: the mouth moves
  bool booting = false;    // slower, softer transitions for the wake-up animation
};

class Face {
 public:
  bool visible = false;   // set by the display lambda: the face page is what the panel shows

  void update(const Input &in, uint32_t now) {
    in_ = in;
    schedule_idle(now);
    target_ = build_target();
    ease(now);
  }

  // True when a redraw changes the picture: the face is still moving, or an effect is running.
  bool needs_frame(uint32_t now) const {
    if (!settled_ || in_.speaking) return true;
    if (in_.voice == Voice::Listening || in_.voice == Voice::Thinking) return true;
    return blinking(now) || due(now, next_blink_) || due(now, next_gaze_);
  }

  template <typename It, typename Color>
  void draw(It &it, Color fg, Color bg, uint32_t now) const {
    Frame f;
    f.shape = cur_;
    f.hearts = hearts_;
    f.heart_size = 56 + 4 * sinf(now / 220.0f);

    f.blink = blink_amount(now);
    if (in_.speaking) {
      f.shape.mouth_w = 34;
      f.shape.mouth_open = 8 + 16 * (0.5f + 0.5f * sinf(now / 70.0f));
    }
    if (in_.voice == Voice::Listening) f.ring = (now / 250) % 3 * 3;
    if (in_.voice == Voice::Thinking) f.dots = (now / 350) % 3;

    cgotchi::face::draw(it, f, fg, bg);
  }

 private:
  static constexpr uint32_t kBlinkMs = 180;

  Input in_;
  Shape cur_ = asleep_shape();   // what is on screen; starts closed so the boot animation opens it
  Shape target_;
  bool hearts_ = false;
  bool settled_ = false;
  uint32_t last_ms_ = 0;

  uint32_t next_blink_ = 3000, next_gaze_ = 4500;
  uint32_t blink_start_ = 0xFFFFF000u;   // long ago: no blink in progress at power on
  float gaze_x_ = 0, gaze_y_ = 0;
  uint32_t rng_ = 2463534242u;

  static bool due(uint32_t now, uint32_t at) { return (int32_t) (now - at) >= 0; }
  bool blinking(uint32_t now) const { return now - blink_start_ < kBlinkMs; }

  // 0 open .. 1 shut .. 0 open, a triangle over the blink.
  float blink_amount(uint32_t now) const {
    if (!blinking(now)) return 0;
    const float t = (now - blink_start_) / (float) kBlinkMs;
    return 1 - fabsf(2 * t - 1);
  }

  uint32_t random(uint32_t range) {
    rng_ ^= rng_ << 13;
    rng_ ^= rng_ >> 17;
    rng_ ^= rng_ << 5;
    return rng_ % range;
  }

  bool idle_life() const { return in_.voice == Voice::Idle && in_.expression != Expression::Sleepy; }

  // Blink every few seconds (sometimes twice) and glance around now and then.
  void schedule_idle(uint32_t now) {
    if (due(now, next_blink_)) {
      blink_start_ = now;
      next_blink_ = now + (random(100) < 15 ? 300 : 2500 + random(3500));
    }
    if (due(now, next_gaze_)) {
      next_gaze_ = now + 2500 + random(4000);
      const bool recenter = random(100) < 45;
      gaze_x_ = recenter ? 0 : (float) ((int) random(21) - 10);
      gaze_y_ = recenter ? 0 : (float) ((int) random(13) - 6);
    }
  }

  Shape build_target() {
    const Look &look = looks()[(size_t) in_.expression];
    Shape s = look.shape;
    hearts_ = look.hearts && in_.voice == Voice::Idle && !in_.speaking;

    switch (in_.voice) {
      case Voice::Listening:   // wide open, waiting
        s.eye_w = 58;
        s.eye_h = 70;
        s.eye_r = 28;
        s.lid_top = s.lid_tilt = s.lid_asym = s.lid_bot = s.wink = 0;
        s.mouth_w = 18;
        s.mouth_open = 18;
        s.mouth_y = 205;
        break;
      case Voice::Thinking:    // glancing up and aside
        s.look_x = 10;
        s.look_y = -16;
        s.mouth_open = 0;
        break;
      case Voice::Error:
        s = looks()[(size_t) Expression::Sad].shape;
        break;
      default:
        break;
    }
    if (idle_life()) {
      s.look_x += gaze_x_;
      s.look_y += gaze_y_;
    }
    return s;
  }

  // Moves every field a fraction of the way to its target (exponential ease, frame rate independent).
  void ease(uint32_t now) {
    float dt = (float) (now - last_ms_);
    last_ms_ = now;
    if (dt > 200) dt = 200;   // a long gap (page was hidden) should not jump or overshoot
    const float tau = in_.booting ? 330.0f : 90.0f;
    const float k = 1 - expf(-dt / tau);

    bool settled = true;
    for (Field f : kFields) {
      const float d = target_.*f - cur_.*f;
      if (fabsf(d) < 0.3f) {
        cur_.*f = target_.*f;
      } else {
        cur_.*f += d * k;
        settled = false;
      }
    }
    settled_ = settled;
  }
};

inline Face &instance() {
  static Face face;
  return face;
}

}  // namespace face
}  // namespace cgotchi
