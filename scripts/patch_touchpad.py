from pathlib import Path
import re

root = Path("gmrunner")
host = root / "src/platform/sdl/Host.h"
s = host.read_text()
old = "struct TouchPad {\n    bool visible = false;"
new = """struct TouchPad {
    bool visible = false;
    bool editMode = false, layoutLoaded = false;
    double sizeScale = 1.0;
    double customX[GP_BUTTON_COUNT] = {}, customY[GP_BUTTON_COUNT] = {};
    bool custom[GP_BUTTON_COUNT] = {};
    void loadLayout();
    void saveLayout();"""
if old not in s:
    raise SystemExit("TouchPad fields anchor not found")
s = s.replace(old, new, 1)
old = "    void draw(Renderer& r, int screenW, int screenH);"
new = "    void draw(Renderer& r, int screenW, int screenH, double fps = 0.0, bool showFps = false);"
if old not in s:
    raise SystemExit("TouchPad draw declaration not found")
s = s.replace(old, new, 1)
host.write_text(s)

touch = r'''// Editable on-screen controller for Android/touchscreen targets.
#include <algorithm>
#include <cmath>
#include <cstdio>

#include "platform/sdl/Host.h"
#include "platform/sdl/Ui.h"
#include "runtime/Runner.h"

namespace gm::host {
namespace {
struct Control {
    int button;
    double x, y, r;
    const char* label;
};

std::vector<Control> layout(int w, int h, const double inset[4], const bool* shown,
                            const TouchPad& pad) {
    double s = std::min(w, h), m = 0.05 * s;
    double rb = 0.068 * s * pad.sizeScale;
    double d = 0.115 * s * pad.sizeScale;
    double x0 = inset[0], y0 = inset[1], x1 = w - inset[2], y1 = h - inset[3];
    double fx = x1 - m - d - rb, fy = y1 - m - d - rb;
    double cx = x0 + m + 0.15 * s, cy = y1 - m - 0.19 * s;
    double dr = rb;
    double sy = x1 - x0 < y1 - y0 ? y1 - m - 0.43 * s : y1 - m - 0.035 * s;
    std::vector<Control> all = {
        {GP_PADU, cx, cy - dr * 1.35, dr, "UP"},
        {GP_PADD, cx, cy + dr * 1.35, dr, "DN"},
        {GP_PADL, cx - dr * 1.35, cy, dr, "<"},
        {GP_PADR, cx + dr * 1.35, cy, dr, ">"},
        {GP_FACE1, fx, fy + d, rb, "A"},
        {GP_FACE2, fx + d, fy, rb, "B"},
        {GP_FACE3, fx - d, fy, rb, "X"},
        {GP_FACE4, fx, fy - d, rb, "Y"},
        {GP_SHOULDERL, x0 + m + 0.06 * s, y0 + m + 0.06 * s, 0.06 * s * pad.sizeScale, "L"},
        {GP_SHOULDERR, x1 - m - 0.06 * s, y0 + m + 0.06 * s, 0.06 * s * pad.sizeScale, "R"},
        {GP_SELECT, (x0 + x1) / 2 - 0.09 * s, sy, 0.045 * s * pad.sizeScale, "SEL"},
        {GP_START, (x0 + x1) / 2 + 0.09 * s, sy, 0.045 * s * pad.sizeScale, "START"},
    };
    for (auto& c : all) {
        if (c.button >= 0 && pad.custom[c.button]) {
            c.x = pad.customX[c.button] * w;
            c.y = pad.customY[c.button] * h;
        }
    }
    if (!shown) return all;
    std::vector<Control> result;
    for (auto& c : all)
        if (shown[c.button]) result.push_back(c);
    return result;
}

int hit(const std::vector<Control>& cs, double x, double y) {
    int best = -1;
    double bestD = 1e9;
    for (size_t i = 0; i < cs.size(); i++) {
        double dist = std::hypot(x - cs[i].x, y - cs[i].y);
        double reach = cs[i].r * 1.4;
        if (dist < reach && dist / cs[i].r < bestD)
            best = static_cast<int>(i), bestD = dist / cs[i].r;
    }
    return best;
}
}  // namespace

TouchPad::~TouchPad() = default;

void TouchPad::loadLayout() {
    if (layoutLoaded) return;
    layoutLoaded = true;
    char* dir = SDL_GetPrefPath("gmRunner", "TagAfterSchool");
    if (!dir) return;
    std::string path = std::string(dir) + "touch-layout.cfg";
    SDL_free(dir);
    FILE* f = std::fopen(path.c_str(), "r");
    if (!f) return;
    double scale = 1.0;
    if (std::fscanf(f, "%lf", &scale) == 1) sizeScale = std::clamp(scale, 0.65, 1.8);
    int button = 0;
    double x = 0, y = 0;
    while (std::fscanf(f, "%d %lf %lf", &button, &x, &y) == 3) {
        if (button >= 0 && button < GP_BUTTON_COUNT && x >= 0 && x <= 1 && y >= 0 && y <= 1) {
            custom[button] = true;
            customX[button] = x;
            customY[button] = y;
        }
    }
    std::fclose(f);
}

void TouchPad::saveLayout() {
    char* dir = SDL_GetPrefPath("gmRunner", "TagAfterSchool");
    if (!dir) return;
    std::string path = std::string(dir) + "touch-layout.cfg";
    SDL_free(dir);
    FILE* f = std::fopen(path.c_str(), "w");
    if (!f) return;
    std::fprintf(f, "%.4f\n", sizeScale);
    for (int i = 0; i < GP_BUTTON_COUNT; ++i)
        if (custom[i]) std::fprintf(f, "%d %.6f %.6f\n", i, customX[i], customY[i]);
    std::fclose(f);
}

bool TouchPad::handleFinger(const SDL_TouchFingerEvent& e, Runner& rt, int w, int h) {
    if (!visible) return false;
    loadLayout();
    double x = e.x * w, y = e.y * h;
    // Small top-right toolbar: EDIT toggles layout mode; +/- resize all controls.
    if (e.type == SDL_FINGERDOWN && y < 64 && x > w - 154) {
        if (x > w - 62) editMode = !editMode;
        else if (editMode && x > w - 105) sizeScale = std::min(1.8, sizeScale + 0.1);
        else if (editMode) sizeScale = std::max(0.65, sizeScale - 0.1);
        saveLayout();
        return true;
    }

    auto cs = layout(w, h, inset, buttons ? buttons->maps[0].onScreen : nullptr, *this);
    Finger* f = nullptr;
    for (auto& fi : fingers)
        if (fi.used && fi.id == e.fingerId) f = &fi;

    if (e.type == SDL_FINGERDOWN) {
        int c = hit(cs, x, y);
        if (c < 0) return false;
        for (auto& fi : fingers) if (!fi.used) { f = &fi; break; }
        if (!f) return true;
        *f = {e.fingerId, c, true, x, y};
        if (editMode) {
            const int b = cs[static_cast<size_t>(c)].button;
            custom[b] = true;
            customX[b] = x / w;
            customY[b] = y / h;
            return true;
        }
    }
    if (!f) return false;
    f->x = x;
    f->y = y;
    if (editMode) {
        const int b = cs[static_cast<size_t>(f->control)].button;
        custom[b] = true;
        customX[b] = std::clamp(x / w, 0.03, 0.97);
        customY[b] = std::clamp(y / h, 0.06, 0.94);
        if (e.type == SDL_FINGERUP) {
            f->used = false;
            saveLayout();
        }
        return true;
    }
    if (e.type == SDL_FINGERUP) f->used = false;
    else if (e.type == SDL_FINGERMOTION) {
        int c = hit(cs, x, y);
        if (c >= 0) f->control = c;
    }

    bool want[GP_BUTTON_COUNT] = {};
    for (auto& fi : fingers) {
        if (!fi.used) continue;
        const Control& c = cs[static_cast<size_t>(fi.control)];
        want[c.button] = true;
    }
    for (int b = 0; b < GP_BUTTON_COUNT; ++b)
        if (want[b] != down[b]) {
            down[b] = want[b];
            if (buttons) buttons->press(rt, Buttons::kOnScreen, b, want[b]);
        }
    return true;
}

void TouchPad::releaseAll(Runner& rt) {
    for (auto& f : fingers) f.used = false;
    for (int b = 0; b < GP_BUTTON_COUNT; ++b)
        if (down[b]) {
            down[b] = false;
            if (buttons) buttons->press(rt, Buttons::kOnScreen, b, false);
        }
}

void TouchPad::draw(Renderer& r, int w, int h, double fps, bool showFps) {
    loadLayout();
    if (!visible && !showFps) return;
    if (!painter || painterOwner != &r) painter = std::make_unique<Painter>(r), painterOwner = &r;
    Painter& p = *painter;
    const uint32_t white = rgb(255, 255, 255), dark = rgb(0, 0, 0);
    if (visible) {
        for (auto& c : layout(w, h, inset, buttons ? buttons->maps[0].onScreen : nullptr, *this)) {
            bool on = c.button >= 0 && down[c.button];
            p.circle(c.x, c.y, c.r, on ? white : dark, on ? 0.48 : 0.27);
            p.ring(c.x, c.y, c.r, std::max(1.0, c.r * 0.08), white, 0.48);
            size_t n = std::string(c.label).size();
            double px = std::max(1.0, std::floor(std::min(c.r * 0.1, 1.5 * c.r / (6.0 * n))));
            p.textCentered(c.x, c.y, px, c.label, white, on ? 0.95 : 0.7);
        }
        double s = std::min(w, h);
        double ty = std::max(18.0, s * 0.035);
        p.circle(w - 38, 30, 25, dark, 0.55);
        p.textCentered(w - 38, 30, std::max(2.0, s * 0.009), editMode ? "ON" : "EDIT", white, 0.95);
        if (editMode) {
            p.circle(w - 88, 30, 20, dark, 0.55);
            p.textCentered(w - 88, 30, std::max(2.0, s * 0.012), "-", white, 0.95);
            p.circle(w - 132, 30, 20, dark, 0.55);
            p.textCentered(w - 132, 30, std::max(2.0, s * 0.012), "+", white, 0.95);
        }
        (void)ty;
    }
    if (showFps) {
        const std::string label = std::to_string(static_cast<int>(std::round(fps))) + " FPS";
        p.text(10, 10, std::max(2.0, std::min(w, h) * 0.004), label, white, 0.9);
    }
}
}  // namespace gm::host
'''
(root / "src/platform/sdl/TouchPad.cpp").write_text(touch)

main = root / "src/platform/sdl/Main.cpp"
s = main.read_text()
old = "rt->gfx->screenOverlay = [&input](Renderer& r, int w, int h) {\n            input.touchPad.draw(r, w, h);"
new = "rt->gfx->screenOverlay = [&input, &rt, &opt](Renderer& r, int w, int h) {\n            input.touchPad.draw(r, w, h, rt ? rt->fpsReal : 0.0, opt.showFps);"
if old not in s:
    raise SystemExit("Main screenOverlay anchor not found")
main.write_text(s.replace(old, new, 1))
print("Patched movable/resizable four-way touch controls and realtime FPS.")
