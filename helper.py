import pygame
# Slider class for UI elements (cooked up by ChatGPT-5)
class Slider:
    def __init__(
        self,
        posX: float,
        posY: float,
        trackLength: int,
        *,
        trackThickness: int = 8,
        minValue: float = 0.0,
        maxValue: float = 100.0,
        value: float | None = None,
        stepSize: float = 1.0,
        orientation: str = "horizontal",
        invertAxis: bool = False,
    trackColor: tuple[int, int, int] | None = (70, 70, 70),
        fillColor: tuple[int, int, int] = (200, 200, 200),
        knobColor: tuple[int, int, int] = (255, 255, 255),
        cornerRadius: int = 6,
        knobSize: int = 16,
        borderColor: tuple[int, int, int] | None = None,
        borderWidth: int = 0,
        showValue: bool = False,
        font: pygame.font.Font | None = None,
        labelText: str | None = None,
        labelColor: tuple[int, int, int] = (232, 207, 166),
        allowClickJump: bool = True,
        enabled: bool = True,
        valueFormatter=None,
        onChange=None,
    ):
        # Geometry
        self.posX = int(posX)
        self.posY = int(posY)
        self.trackLength = max(1, int(trackLength))
        self.trackThickness = max(1, int(trackThickness))
        self.orientation = orientation if orientation in ("horizontal", "vertical") else "horizontal"
        self.invertAxis = bool(invertAxis)

        # Value model
        self.minValue = float(minValue)
        self.maxValue = float(maxValue) if maxValue != minValue else float(minValue) + 1.0
        self.stepSize = max(0.000001, float(stepSize))
        self.value = self._clampValue(self.minValue if value is None else float(value))

        # Appearance
        self.trackColor = trackColor
        self.fillColor = fillColor
        self.knobColor = knobColor
        self.cornerRadius = max(0, int(cornerRadius))
        self.knobSize = max(6, int(knobSize))
        self.borderColor = borderColor
        self.borderWidth = max(0, int(borderWidth))
        self.showValue = bool(showValue)
        self.font = font
        self.labelText = labelText
        self.labelColor = labelColor

        # Behavior
        self.allowClickJump = bool(allowClickJump)
        self.enabled = bool(enabled)
        self.valueFormatter = valueFormatter
        self.onChange = onChange

        self.dragging = False
        self._hover = False

        # Precompute rects
        self._recalcRects()

    @property
    def rect(self) -> pygame.Rect:
        knob = self._knobRectForValue(self.value)
        return self._trackRect.union(knob)

    def update(self, events: list) -> bool:
        handledAny = False
        for e in events:
            handledAny |= self.handleEvent(e)
        return handledAny

    # ---------- Public API ----------
    def setValue(self, value: float, *, notify: bool = True):
        oldValue = self.value
        self.value = self._snapToStep(self._clampValue(float(value)))
        if notify and self.onChange and self.value != oldValue:
            try:
                self.onChange(self.value)
            except Exception:
                pass

    def getValue(self) -> float:
        return self.value

    def setRange(self, minValue: float, maxValue: float):
        self.minValue = float(minValue)
        self.maxValue = float(maxValue) if maxValue != minValue else float(minValue) + 1.0
        self.setValue(self.value, notify=False)
        self._recalcRects()

    def setStep(self, stepSize: float):
        self.stepSize = max(0.000001, float(stepSize))
        self.setValue(self.value, notify=False)

    def setPosition(self, posX: int, posY: int):
        self.posX = int(posX)
        self.posY = int(posY)
        self._recalcRects()

    def setSize(self, trackLength: int, trackThickness: int | None = None):
        self.trackLength = max(1, int(trackLength))
        if trackThickness is not None:
            self.trackThickness = max(1, int(trackThickness))
        self._recalcRects()

    def setColors(
        self,
        *,
        trackColor: tuple[int, int, int] | None = None,
        fillColor: tuple[int, int, int] | None = None,
        knobColor: tuple[int, int, int] | None = None,
        borderColor: tuple[int, int, int] | None = None,
        labelColor: tuple[int, int, int] | None = None,
    ):
        if trackColor is not None:
            self.trackColor = trackColor
        if fillColor is not None:
            self.fillColor = fillColor
        if knobColor is not None:
            self.knobColor = knobColor
        if borderColor is not None:
            self.borderColor = borderColor
        if labelColor is not None:
            self.labelColor = labelColor

    def setEnabled(self, enabled: bool):
        self.enabled = bool(enabled)

    def draw(self, surface: pygame.Surface):
        trackRect = self._trackRect
        fillRect = self._fillRectForValue(self.value)

        def dimColor(c: tuple[int, int, int]) -> tuple[int, int, int]:
            return (int(c[0] * 0.5), int(c[1] * 0.5), int(c[2] * 0.5))

        # Track color can be None to indicate transparent background
        if self.trackColor is None:
            trackColor = None
        else:
            trackColor = self.trackColor if self.enabled else dimColor(self.trackColor)

        # Fill/knob colors are always tuples
        fillColor = self.fillColor if self.enabled else dimColor(self.fillColor)
        knobColor = self.knobColor if self.enabled else dimColor(self.knobColor)

        if trackColor is not None:
            pygame.draw.rect(surface, trackColor, trackRect, border_radius=self.cornerRadius)
        pygame.draw.rect(surface, fillColor, fillRect, border_radius=self.cornerRadius)
        if self.borderColor and self.borderWidth > 0:
            pygame.draw.rect(surface, self.borderColor, trackRect, width=self.borderWidth, border_radius=self.cornerRadius)

        knobRect = self._knobRectForValue(self.value)
        pygame.draw.ellipse(surface, knobColor, knobRect)

        if self.showValue and self.font is not None:
            if self.valueFormatter:
                text = self.valueFormatter(self.value)
            else:
                text = f"{self.value:.0f}" if abs(self.maxValue - self.minValue) <= 1000 else f"{self.value:.2f}"
            textSurf = self.font.render(text, True, self.labelColor)
            textPos = (trackRect.right + 8, trackRect.centery - textSurf.get_height() // 2) if self.orientation == "horizontal" else (
                trackRect.left - textSurf.get_width() - 8, trackRect.top - textSurf.get_height() - 4)
            surface.blit(textSurf, textPos)

        if self.labelText and self.font is not None:
            labelSurf = self.font.render(self.labelText, True, self.labelColor)
            labelPos = (trackRect.left, trackRect.top - labelSurf.get_height() - 6)
            surface.blit(labelSurf, labelPos)

    def handleEvent(self, event) -> bool:
        if not self.enabled:
            return False

        handled = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._knobRectForValue(self.value).collidepoint(event.pos) or (
                self.allowClickJump and self._trackRect.inflate(0, self.knobSize).collidepoint(event.pos)
            ):
                self.dragging = True
                self._updateValueFromMouse(event.pos)
                handled = True

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._updateValueFromMouse(event.pos)
            handled = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            handled = True

        return handled

    # ---------- Internal helpers ----------
    def _recalcRects(self):
        if self.orientation == "horizontal":
            self._trackRect = pygame.Rect(self.posX, self.posY, self.trackLength, self.trackThickness)
        else:
            self._trackRect = pygame.Rect(self.posX, self.posY, self.trackThickness, self.trackLength)

    def _valueRange(self) -> float:
        return max(1e-9, self.maxValue - self.minValue)

    def _clampValue(self, v: float) -> float:
        return max(self.minValue, min(self.maxValue, v))

    def _snapToStep(self, v: float) -> float:
        r = (v - self.minValue) / self.stepSize
        return self.minValue + round(r) * self.stepSize

    def _valueToT(self, v: float) -> float:
        t = (v - self.minValue) / self._valueRange()
        if self.invertAxis:
            t = 1.0 - t
        return max(0.0, min(1.0, t))

    def _tToValue(self, t: float) -> float:
        if self.invertAxis:
            t = 1.0 - t
        return self.minValue + t * self._valueRange()

    def _fillRectForValue(self, v: float) -> pygame.Rect:
        t = self._valueToT(v)
        if self.orientation == "horizontal":
            w = int(round(self._trackRect.width * t))
            return pygame.Rect(self._trackRect.left, self._trackRect.top, w, self._trackRect.height)
        else:
            h = int(round(self._trackRect.height * t))
            return pygame.Rect(self._trackRect.left, self._trackRect.top, self._trackRect.width, h)

    def _knobRectForValue(self, v: float) -> pygame.Rect:
        t = self._valueToT(v)
        if self.orientation == "horizontal":
            cx = self._trackRect.left + int(round(self._trackRect.width * t))
            cy = self._trackRect.centery
        else:
            cx = self._trackRect.centerx
            cy = self._trackRect.top + int(round(self._trackRect.height * t))
        return pygame.Rect(cx - self.knobSize // 2, cy - self.knobSize // 2, self.knobSize, self.knobSize)

    def _updateValueFromMouse(self, pos: tuple[int, int]):
        px, py = pos
        if self.orientation == "horizontal":
            t = (px - self._trackRect.left) / max(1.0, self._trackRect.width)
        else:
            t = (py - self._trackRect.top) / max(1.0, self._trackRect.height)
        t = max(0.0, min(1.0, t))
        newValue = self._snapToStep(self._clampValue(self._tToValue(t)))
        if newValue != self.value:
            self.value = newValue
            if self.onChange:
                try:
                    self.onChange(self.value)
                except Exception:
                    pass