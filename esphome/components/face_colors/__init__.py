import esphome.codegen as cg
import esphome.config_validation as cv

# Header-only component: makes FACE_PRESETS (face_colors.h) available to the lambdas in the YAML,
# so the config needs no local includes: file and can be shared as a package.
CODEOWNERS = []
CONFIG_SCHEMA = cv.Schema({})


async def to_code(config):
    cg.add_global(cg.RawStatement('#include "esphome/components/face_colors/face_colors.h"'))
