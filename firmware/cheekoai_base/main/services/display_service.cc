#include "services/display_service.h"

#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_check.h"
#include "esp_lcd_jd9853.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_log.h"
#include "esp_lvgl_port.h"

namespace cheekoai {

namespace {

const char* TAG = "display";

// Pins and panel size from boards/cheeko-gotchi/board.json and SKILL.md.
constexpr gpio_num_t kPinDc = GPIO_NUM_8;
constexpr gpio_num_t kPinSclk = GPIO_NUM_9;
constexpr gpio_num_t kPinMosi = GPIO_NUM_10;
constexpr gpio_num_t kPinBacklight = GPIO_NUM_13;
constexpr gpio_num_t kPinCs = GPIO_NUM_14;
constexpr gpio_num_t kPinReset = GPIO_NUM_17;
constexpr int kWidth = 240;
constexpr int kHeight = 296;
constexpr spi_host_device_t kSpiHost = SPI2_HOST;
constexpr int kLvglBufferRows = 20;  // LVGL draws the screen in strips of this many rows

// JD9853 2.01" 240x296 panel init sequence (copied from firmware/hardware_test).
const jd9853_lcd_init_cmd_t kPanelInit[] = {
    {0xDF, (uint8_t[]){0x98, 0x53}, 2, 0},
    {0xDE, (uint8_t[]){0x00}, 1, 0},
    {0xB2, (uint8_t[]){0x25}, 1, 0},
    {0xB7, (uint8_t[]){0x00, 0x29, 0x00, 0x51}, 4, 0},
    {0xBB, (uint8_t[]){0x4F, 0x1A, 0x55, 0x73, 0x63, 0xF0}, 6, 0},
    {0xC0, (uint8_t[]){0x44, 0xA4}, 2, 0},
    {0xC1, (uint8_t[]){0x12}, 1, 0},
    {0xC3, (uint8_t[]){0x7D, 0x07, 0x14, 0x06, 0xC8, 0x71, 0x6C, 0x77}, 8, 0},
    {0xC4, (uint8_t[]){0x00, 0x00, 0x94, 0x79, 0x25, 0x0A, 0x16, 0x79, 0x25, 0x0A, 0x16, 0x82}, 12, 0},
    {0xC8, (uint8_t[]){0x3F, 0x34, 0x2D, 0x26, 0x2B, 0x2B, 0x25, 0x24, 0x23, 0x22, 0x20, 0x17, 0x14, 0x0E, 0x06, 0x00,
                       0x3F, 0x34, 0x2D, 0x26, 0x2B, 0x2B, 0x25, 0x24, 0x23, 0x22, 0x20, 0x17, 0x14, 0x0E, 0x06, 0x00}, 32, 0},
    {0xD0, (uint8_t[]){0x04, 0x06, 0x6B, 0x0F, 0x00}, 5, 0},
    {0xD7, (uint8_t[]){0x00, 0x30}, 2, 0},
    {0xE6, (uint8_t[]){0x10}, 1, 0},
    {0xDE, (uint8_t[]){0x01}, 1, 0},
    {0xB7, (uint8_t[]){0x03, 0x13, 0xEF, 0x35, 0x35}, 5, 0},
    {0xC1, (uint8_t[]){0x14, 0x15, 0xC0}, 3, 0},
    {0xC2, (uint8_t[]){0x06, 0x3A}, 2, 0},
    {0xC4, (uint8_t[]){0x72, 0x12}, 2, 0},
    {0xBE, (uint8_t[]){0x00}, 1, 0},
    {0xDE, (uint8_t[]){0x00}, 1, 0},
    {0x35, (uint8_t[]){0x00}, 1, 0},
    {0x3A, (uint8_t[]){0x05}, 1, 0},                    // RGB565
    {0x2A, (uint8_t[]){0x00, 0x00, 0x00, 0xEF}, 4, 0},  // CASET 0..239
    {0x2B, (uint8_t[]){0x00, 0x00, 0x01, 0x27}, 4, 0},  // RASET 0..295
    {0x11, (uint8_t[]){0x00}, 0, 120},                  // sleep out
    {0x29, (uint8_t[]){0x00}, 0, 10},                   // display on
};

esp_lcd_panel_io_handle_t g_io = nullptr;
esp_lcd_panel_handle_t g_panel = nullptr;
lv_display_t* g_lv_display = nullptr;

}  // namespace

void DisplayService::Initialize() {
  // Keep the backlight off until the first frame so the user never sees noise.
  gpio_config_t bl = {};
  bl.pin_bit_mask = 1ULL << kPinBacklight;
  bl.mode = GPIO_MODE_OUTPUT;
  gpio_config(&bl);
  gpio_set_level(kPinBacklight, 0);

  // The JD9853_PANEL_BUS_SPI_CONFIG macro from the driver header is written for
  // C; its designated initialisers are rejected by C++, so fill the fields in.
  spi_bus_config_t bus = {};
  bus.sclk_io_num = kPinSclk;
  bus.mosi_io_num = kPinMosi;
  bus.miso_io_num = -1;
  bus.quadwp_io_num = -1;
  bus.quadhd_io_num = -1;
  bus.max_transfer_sz = kWidth * 40 * 2;
  ESP_ERROR_CHECK(spi_bus_initialize(kSpiHost, &bus, SPI_DMA_CH_AUTO));

  esp_lcd_panel_io_spi_config_t io_cfg = JD9853_PANEL_IO_SPI_CONFIG(kPinCs, kPinDc, nullptr, nullptr);  // LVGL port adds its own callback
  ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi(static_cast<esp_lcd_spi_bus_handle_t>(kSpiHost), &io_cfg, &g_io));

  jd9853_vendor_config_t vendor = {};
  vendor.init_cmds = kPanelInit;
  vendor.init_cmds_size = sizeof(kPanelInit) / sizeof(kPanelInit[0]);

  esp_lcd_panel_dev_config_t panel_cfg = {};
  panel_cfg.reset_gpio_num = kPinReset;
  // RGB order gives correct colours with this LVGL setup (verified on the
  // device); hardware_test uses BGR.
  panel_cfg.rgb_endian = LCD_RGB_ENDIAN_RGB;
  panel_cfg.bits_per_pixel = 16;
  panel_cfg.vendor_config = &vendor;

  ESP_ERROR_CHECK(esp_lcd_new_panel_jd9853(g_io, &panel_cfg, &g_panel));
  ESP_ERROR_CHECK(esp_lcd_panel_reset(g_panel));
  ESP_ERROR_CHECK(esp_lcd_panel_init(g_panel));
  ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(g_panel, true));

  // LVGL runs in its own task; esp_lvgl_port starts it and sends each drawn
  // strip to the panel over DMA. Settings match firmware/hardware_test.
  lvgl_port_cfg_t port_cfg = ESP_LVGL_PORT_INIT_CONFIG();
  port_cfg.task_stack = 6144;
  ESP_ERROR_CHECK(lvgl_port_init(&port_cfg));

  lvgl_port_display_cfg_t disp_cfg = {};
  disp_cfg.io_handle = g_io;
  disp_cfg.panel_handle = g_panel;
  disp_cfg.buffer_size = kWidth * kLvglBufferRows;
  disp_cfg.hres = kWidth;
  disp_cfg.vres = kHeight;
  disp_cfg.color_format = LV_COLOR_FORMAT_RGB565;
  disp_cfg.flags.buff_dma = 1;
  disp_cfg.flags.swap_bytes = 1;  // panel reads the high byte first
  g_lv_display = lvgl_port_add_disp(&disp_cfg);
  ESP_ERROR_CHECK(g_lv_display != nullptr ? ESP_OK : ESP_FAIL);

  Clear(0x000000);
  gpio_set_level(kPinBacklight, 1);
  ESP_LOGI(TAG, "JD9853 %dx%d ready", kWidth, kHeight);
}

void DisplayService::Clear(uint32_t rgb) {
  if (g_lv_display == nullptr || !lvgl_port_lock(0)) {
    return;
  }
  lv_obj_t* screen = lv_screen_active();
  lv_obj_clean(screen);  // delete everything previously drawn
  lv_obj_set_style_bg_color(screen, lv_color_hex(rgb), 0);
  lv_obj_set_style_bg_opa(screen, LV_OPA_COVER, 0);
  lvgl_port_unlock();
}

void DisplayService::CenterText(int y, const std::string& text) {
  if (g_lv_display == nullptr || !lvgl_port_lock(0)) {
    return;
  }
  lv_obj_t* label = lv_label_create(lv_screen_active());
  lv_obj_set_width(label, kWidth);  // full width, so centred text is centred on screen
  lv_obj_set_pos(label, 0, y);
  lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, 0);
  lv_obj_set_style_text_font(label, &lv_font_montserrat_24, 0);
  lv_obj_set_style_text_color(label, lv_color_hex(0xFFFFFF), 0);
  lv_label_set_text(label, text.c_str());
  lvgl_port_unlock();
}

void DisplayService::ShowBootSplash(const std::string& product_name) {
  Clear(0x101820);
  CenterText(72, product_name);
}

void DisplayService::ShowPairingCode(const std::string& code) {
  (void)code;
  // TODO(ui): Render pairing QR and short code.
}

void DisplayService::ShowRecovery(const std::string& reason) {
  (void)reason;
  // TODO(ui): Render recovery instructions and support code.
}

void DisplayService::ShowLauncher() {
  // TODO(ui): Render installed app launcher or default Cheeko face.
}

}  // namespace cheekoai
