#pragma once

#include <cstdint>
#include <string>

namespace cheekoai {

class DisplayService {
 public:
  void Initialize();
  // Clear everything on screen and set the background. `rgb` is 0xRRGGBB.
  void Clear(uint32_t rgb);
  // Draw white text horizontally centred, `y` pixels from the top.
  void CenterText(int y, const std::string& text);
  void ShowBootSplash(const std::string& product_name);
  void ShowPairingCode(const std::string& code);
  void ShowRecovery(const std::string& reason);
  void ShowLauncher();
};

}  // namespace cheekoai
