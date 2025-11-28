'use client'

import { cn } from '@/lib/utils'

interface LEDPixel {
  r: number
  g: number
  b: number
}

interface LEDPanelPreviewProps {
  pixels: LEDPixel[][]  // 64x64 array of RGB values
  pixelSize?: number    // Size of each LED pixel in pixels (default 4)
  className?: string
}

/**
 * LED Panel Preview Component
 *
 * Renders a 1:1 representation of the 64x64 LED matrix display.
 * Shows exactly what the physical LED panel will display.
 */
export function LEDPanelPreview({ pixels, pixelSize = 4, className }: LEDPanelPreviewProps) {
  // Default to black pixels if no data
  const defaultPixels: LEDPixel[][] = Array.from({ length: 64 }, () =>
    Array.from({ length: 64 }, () => ({ r: 0, g: 0, b: 0 }))
  )

  const displayPixels = pixels.length === 64 ? pixels : defaultPixels

  return (
    <div className={cn('inline-block', className)}>
      <div
        className="bg-black border-2 border-gray-700 rounded-sm overflow-hidden"
        style={{
          width: `${64 * pixelSize}px`,
          height: `${64 * pixelSize}px`,
        }}
      >
        <div className="grid grid-rows-64 gap-0">
          {displayPixels.map((row, y) => (
            <div key={y} className="grid grid-cols-64 gap-0">
              {row.map((pixel, x) => (
                <div
                  key={`${x}-${y}`}
                  className="transition-colors duration-100"
                  style={{
                    width: `${pixelSize}px`,
                    height: `${pixelSize}px`,
                    backgroundColor: `rgb(${pixel.r}, ${pixel.g}, ${pixel.b})`,
                  }}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="text-xs text-gray-500 text-center mt-2">
        64×64 LED Panel Preview
      </div>
    </div>
  )
}

/**
 * Helper function to generate LED pixel data for different layout types.
 * This mimics the Python LED renderer logic in TypeScript.
 */

interface GaugeData {
  id?: string
  label: string
  percentage: number
  type?: 'project' | 'sprint' | 'user_story'
  children?: GaugeData[]
}

interface ProjectData {
  id: string
  name: string
  progress: {
    percentage: number
  }
}

interface SprintData {
  id: string
  name: string
  progress: {
    percentage: number
  }
  user_stories?: UserStoryData[]
}

interface UserStoryData {
  id: string
  title: string
  progress: {
    percentage: number
  }
}

// Color scheme matching LED hardware
const COLOR_PROJECT = { r: 0, g: 100, b: 255 }    // Blue
const COLOR_SPRINT = { r: 0, g: 255, b: 0 }       // Green
const COLOR_USER_STORY = { r: 255, g: 255, b: 0 } // Yellow
const COLOR_OFF = { r: 0, g: 0, b: 0 }            // Black/off

function createEmptyPixels(): LEDPixel[][] {
  return Array.from({ length: 64 }, () =>
    Array.from({ length: 64 }, () => ({ ...COLOR_OFF }))
  )
}

function fillVerticalBar(
  pixels: LEDPixel[][],
  xStart: number,
  xEnd: number,
  yStart: number,
  yEnd: number,
  percentage: number,
  color: LEDPixel
): void {
  const height = yEnd - yStart
  const fillHeight = Math.floor((percentage / 100) * height)

  for (let i = 0; i < fillHeight; i++) {
    const y = yEnd - 1 - i // Start from bottom
    for (let x = xStart; x < xEnd; x++) {
      if (x >= 0 && x < 64 && y >= 0 && y < 64) {
        pixels[y][x] = { ...color }
      }
    }
  }
}

function fillHorizontalBar(
  pixels: LEDPixel[][],
  xStart: number,
  xEnd: number,
  yStart: number,
  yEnd: number,
  percentage: number,
  color: LEDPixel
): void {
  const width = xEnd - xStart
  const fillWidth = Math.floor((percentage / 100) * width)

  for (let x = 0; x < fillWidth; x++) {
    const actualX = xStart + x
    for (let y = yStart; y < yEnd; y++) {
      if (actualX >= 0 && actualX < 64 && y >= 0 && y < 64) {
        pixels[y][actualX] = { ...color }
      }
    }
  }
}

function drawOutlineRectangle(
  pixels: LEDPixel[][],
  xStart: number,
  xEnd: number,
  yStart: number,
  yEnd: number,
  color: LEDPixel
): void {
  // Draw top and bottom edges
  for (let x = xStart; x < xEnd; x++) {
    if (x >= 0 && x < 64) {
      if (yStart >= 0 && yStart < 64) {
        pixels[yStart][x] = { ...color }
      }
      if (yEnd - 1 >= 0 && yEnd - 1 < 64) {
        pixels[yEnd - 1][x] = { ...color }
      }
    }
  }

  // Draw left and right edges
  for (let y = yStart; y < yEnd; y++) {
    if (y >= 0 && y < 64) {
      if (xStart >= 0 && xStart < 64) {
        pixels[y][xStart] = { ...color }
      }
      if (xEnd - 1 >= 0 && xEnd - 1 < 64) {
        pixels[y][xEnd - 1] = { ...color }
      }
    }
  }
}

// 3x5 font for digits, letters, and special characters
const FONT_3X5: Record<string, number[][]> = {
  // Digits
  '0': [[1,1,1],[1,0,1],[1,0,1],[1,0,1],[1,1,1]],
  '1': [[0,1,0],[1,1,0],[0,1,0],[0,1,0],[1,1,1]],
  '2': [[1,1,1],[0,0,1],[1,1,1],[1,0,0],[1,1,1]],
  '3': [[1,1,1],[0,0,1],[1,1,1],[0,0,1],[1,1,1]],
  '4': [[1,0,1],[1,0,1],[1,1,1],[0,0,1],[0,0,1]],
  '5': [[1,1,1],[1,0,0],[1,1,1],[0,0,1],[1,1,1]],
  '6': [[1,1,1],[1,0,0],[1,1,1],[1,0,1],[1,1,1]],
  '7': [[1,1,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1]],
  '8': [[1,1,1],[1,0,1],[1,1,1],[1,0,1],[1,1,1]],
  '9': [[1,1,1],[1,0,1],[1,1,1],[0,0,1],[1,1,1]],
  // Uppercase letters
  'A': [[0,1,0],[1,0,1],[1,1,1],[1,0,1],[1,0,1]],
  'B': [[1,1,0],[1,0,1],[1,1,0],[1,0,1],[1,1,0]],
  'C': [[1,1,1],[1,0,0],[1,0,0],[1,0,0],[1,1,1]],
  'D': [[1,1,0],[1,0,1],[1,0,1],[1,0,1],[1,1,0]],
  'E': [[1,1,1],[1,0,0],[1,1,1],[1,0,0],[1,1,1]],
  'F': [[1,1,1],[1,0,0],[1,1,0],[1,0,0],[1,0,0]],
  'G': [[1,1,1],[1,0,0],[1,0,1],[1,0,1],[1,1,1]],
  'H': [[1,0,1],[1,0,1],[1,1,1],[1,0,1],[1,0,1]],
  'I': [[1,1,1],[0,1,0],[0,1,0],[0,1,0],[1,1,1]],
  'J': [[0,0,1],[0,0,1],[0,0,1],[1,0,1],[1,1,1]],
  'K': [[1,0,1],[1,0,1],[1,1,0],[1,0,1],[1,0,1]],
  'L': [[1,0,0],[1,0,0],[1,0,0],[1,0,0],[1,1,1]],
  'M': [[1,0,1],[1,1,1],[1,0,1],[1,0,1],[1,0,1]],
  'N': [[1,0,1],[1,1,1],[1,1,1],[1,0,1],[1,0,1]],
  'O': [[1,1,1],[1,0,1],[1,0,1],[1,0,1],[1,1,1]],
  'P': [[1,1,1],[1,0,1],[1,1,1],[1,0,0],[1,0,0]],
  'Q': [[1,1,1],[1,0,1],[1,0,1],[1,1,1],[0,0,1]],
  'R': [[1,1,0],[1,0,1],[1,1,0],[1,0,1],[1,0,1]],
  'S': [[1,1,1],[1,0,0],[1,1,1],[0,0,1],[1,1,1]],
  'T': [[1,1,1],[0,1,0],[0,1,0],[0,1,0],[0,1,0]],
  'U': [[1,0,1],[1,0,1],[1,0,1],[1,0,1],[1,1,1]],
  'V': [[1,0,1],[1,0,1],[1,0,1],[1,0,1],[0,1,0]],
  'W': [[1,0,1],[1,0,1],[1,0,1],[1,1,1],[1,0,1]],
  'X': [[1,0,1],[1,0,1],[0,1,0],[1,0,1],[1,0,1]],
  'Y': [[1,0,1],[1,0,1],[1,1,1],[0,1,0],[0,1,0]],
  'Z': [[1,1,1],[0,0,1],[0,1,0],[1,0,0],[1,1,1]],
  // Lowercase letters (same as uppercase for simplicity on 3x5 grid)
  'a': [[0,1,0],[1,0,1],[1,1,1],[1,0,1],[1,0,1]],
  'b': [[1,1,0],[1,0,1],[1,1,0],[1,0,1],[1,1,0]],
  'c': [[1,1,1],[1,0,0],[1,0,0],[1,0,0],[1,1,1]],
  'd': [[1,1,0],[1,0,1],[1,0,1],[1,0,1],[1,1,0]],
  'e': [[1,1,1],[1,0,0],[1,1,1],[1,0,0],[1,1,1]],
  'f': [[1,1,1],[1,0,0],[1,1,0],[1,0,0],[1,0,0]],
  'g': [[1,1,1],[1,0,0],[1,0,1],[1,0,1],[1,1,1]],
  'h': [[1,0,1],[1,0,1],[1,1,1],[1,0,1],[1,0,1]],
  'i': [[1,1,1],[0,1,0],[0,1,0],[0,1,0],[1,1,1]],
  'j': [[0,0,1],[0,0,1],[0,0,1],[1,0,1],[1,1,1]],
  'k': [[1,0,1],[1,0,1],[1,1,0],[1,0,1],[1,0,1]],
  'l': [[1,0,0],[1,0,0],[1,0,0],[1,0,0],[1,1,1]],
  'm': [[1,0,1],[1,1,1],[1,0,1],[1,0,1],[1,0,1]],
  'n': [[1,0,1],[1,1,1],[1,1,1],[1,0,1],[1,0,1]],
  'o': [[1,1,1],[1,0,1],[1,0,1],[1,0,1],[1,1,1]],
  'p': [[1,1,1],[1,0,1],[1,1,1],[1,0,0],[1,0,0]],
  'q': [[1,1,1],[1,0,1],[1,0,1],[1,1,1],[0,0,1]],
  'r': [[1,1,0],[1,0,1],[1,1,0],[1,0,1],[1,0,1]],
  's': [[1,1,1],[1,0,0],[1,1,1],[0,0,1],[1,1,1]],
  't': [[1,1,1],[0,1,0],[0,1,0],[0,1,0],[0,1,0]],
  'u': [[1,0,1],[1,0,1],[1,0,1],[1,0,1],[1,1,1]],
  'v': [[1,0,1],[1,0,1],[1,0,1],[1,0,1],[0,1,0]],
  'w': [[1,0,1],[1,0,1],[1,0,1],[1,1,1],[1,0,1]],
  'x': [[1,0,1],[1,0,1],[0,1,0],[1,0,1],[1,0,1]],
  'y': [[1,0,1],[1,0,1],[1,1,1],[0,1,0],[0,1,0]],
  'z': [[1,1,1],[0,0,1],[0,1,0],[1,0,0],[1,1,1]],
  // Special characters
  '%': [[1,0,1],[0,0,1],[0,1,0],[1,0,0],[1,0,1]],
  ':': [[0,0,0],[0,1,0],[0,0,0],[0,1,0],[0,0,0]],
  '/': [[0,0,1],[0,0,1],[0,1,0],[1,0,0],[1,0,0]],
  '-': [[0,0,0],[0,0,0],[1,1,1],[0,0,0],[0,0,0]],
  ' ': [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]],
}

// Checkmark colors
const COLOR_CHECK_BG = { r: 0, g: 200, b: 0 }     // Green background
const COLOR_CHECK_WHITE = { r: 255, g: 255, b: 255 } // White checkmark

/**
 * Draw a white checkmark in a green box (7x7 pixels)
 * Used to indicate 100% completion
 */
function drawCheckmark(
  pixels: LEDPixel[][],
  x: number,
  y: number
): void {
  // 7x7 checkmark pattern: 0 = green bg, 1 = white checkmark
  const pattern = [
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1, 0, 0],
    [0, 1, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
  ]

  for (let row = 0; row < 7; row++) {
    for (let col = 0; col < 7; col++) {
      const pixelX = x + col
      const pixelY = y + row
      if (pixelX >= 0 && pixelX < 64 && pixelY >= 0 && pixelY < 64) {
        pixels[pixelY][pixelX] = pattern[row][col] === 1
          ? { ...COLOR_CHECK_WHITE }
          : { ...COLOR_CHECK_BG }
      }
    }
  }
}

function drawText(
  pixels: LEDPixel[][],
  text: string,
  x: number,
  y: number,
  color: LEDPixel
): void {
  let currentX = x

  for (const char of text) {
    const glyph = FONT_3X5[char]
    if (!glyph) {
      currentX += 4 // Space for unknown char
      continue
    }

    // Draw the character
    for (let row = 0; row < glyph.length; row++) {
      for (let col = 0; col < glyph[row].length; col++) {
        if (glyph[row][col] === 1) {
          const pixelX = currentX + col
          const pixelY = y + row
          if (pixelX >= 0 && pixelX < 64 && pixelY >= 0 && pixelY < 64) {
            pixels[pixelY][pixelX] = { ...color }
          }
        }
      }
    }

    currentX += 4 // Move to next character position (3 width + 1 spacing)
  }
}

export function generateSingleViewPixels(
  projectData: ProjectData,
  sprints?: SprintData[]
): LEDPixel[][] {
  const pixels = createEmptyPixels()
  const percentage = projectData.progress?.percentage || 0
  const projectName = projectData.name || 'Project'

  // Calculate sprint counts
  const totalSprints = sprints?.length || 0
  const completedSprints = sprints?.filter(s => s.progress.percentage >= 100).length || 0

  // Calculate user story counts
  const totalStories = sprints?.reduce((sum, s) => sum + (s.user_stories?.length || 0), 0) || 0
  const completedStories = sprints?.reduce((sum, s) =>
    sum + (s.user_stories?.filter(us => us.progress?.percentage >= 100).length || 0), 0) || 0

  // Constants matching backend layout
  const GAUGE_X_START = 22
  const GAUGE_X_END = 42
  const GAUGE_Y_START = 12
  const GAUGE_Y_END = 56

  const GRAY_OUTLINE = { r: 100, g: 100, b: 100 }
  const GREEN_FILL = { r: 0, g: 255, b: 0 }
  const WHITE_TEXT = { r: 255, g: 255, b: 255 }

  // 1. Draw project name at top (row 3-7, using 3x5 font)
  const displayName = projectName.length > 10 ? projectName.substring(0, 10) : projectName
  const nameWidth = displayName.length * 4 - 1
  const nameX = Math.floor((64 - nameWidth) / 2)
  drawText(pixels, displayName, nameX, 3, WHITE_TEXT)

  // 2. Draw vertical gauge outline (gray rectangle)
  drawOutlineRectangle(pixels, GAUGE_X_START, GAUGE_X_END, GAUGE_Y_START, GAUGE_Y_END, GRAY_OUTLINE)

  // 3. Fill vertical gauge with green based on percentage
  fillVerticalBar(
    pixels,
    GAUGE_X_START + 1,
    GAUGE_X_END - 1,
    GAUGE_Y_START + 1,
    GAUGE_Y_END - 1,
    percentage,
    GREEN_FILL
  )

  // 4. Draw sprint and story labels higher up (row 48)
  if (totalSprints > 0) {
    drawText(pixels, "S:", 1, 48, WHITE_TEXT)
  }

  if (totalStories > 0) {
    drawText(pixels, "US:", 48, 48, WHITE_TEXT)
  }

  // 5. Draw sprint and story counts at row 61
  if (totalSprints > 0) {
    const sprintCount = `${completedSprints}/${totalSprints}`
    drawText(pixels, sprintCount, 0, 61, WHITE_TEXT)
  }

  if (totalStories > 0) {
    const storyCount = `${completedStories}/${totalStories}`
    drawText(pixels, storyCount, 48, 61, WHITE_TEXT)
  }

  // 6. Draw percentage text or checkmark centered at bottom (row 64)
  if (percentage >= 100) {
    // Draw checkmark centered (7px wide, center at x=28)
    drawCheckmark(pixels, 28, 57)
  } else {
    const percentText = `${Math.floor(percentage)}%`
    const percentWidth = percentText.length * 4 - 1
    const percentX = Math.floor((64 - percentWidth) / 2)
    drawText(pixels, percentText, percentX, 64, WHITE_TEXT)
  }

  return pixels
}

export function generateSprintViewPixels(
  projectData: ProjectData,
  sprints: SprintData[]
): LEDPixel[][] {
  const pixels = createEmptyPixels()

  // Top horizontal project bar (10px tall, increased from 8px for better visibility)
  const PROJECT_BAR_HEIGHT = 10
  const projectPercentage = projectData.progress?.percentage || 0
  fillHorizontalBar(pixels, 0, 64, 0, PROJECT_BAR_HEIGHT, projectPercentage, COLOR_PROJECT)

  // Add percentage text or checkmark inside project bar (centered)
  if (projectPercentage >= 100) {
    // Draw checkmark centered in project bar (7px wide, center at x=28)
    drawCheckmark(pixels, 28, 1)
  } else {
    const projectText = `${Math.floor(projectPercentage)}%`
    const textWidth = projectText.length * 4 - 1 // Each char is 3 wide + 1 spacing
    const textX = Math.floor((64 - textWidth) / 2)
    const textY = 2 // Centered vertically in 10px bar
    drawText(pixels, projectText, textX, textY, { r: 255, g: 255, b: 255 }) // White text
  }

  // Sprint labels row (rows 11-12)
  const LABEL_ROW = 11

  // Two active sprint bars + one empty slot
  const sprintWidth = Math.floor(64 / 3) // ~21 pixels each

  // Sprint 1
  if (sprints.length >= 1) {
    const sprint1Percentage = sprints[0].progress?.percentage || 0

    // Draw "S1" label
    drawText(pixels, 'S1', 7, LABEL_ROW, { r: 255, g: 255, b: 255 })

    // Draw sprint bar
    fillVerticalBar(pixels, 0, sprintWidth, 13, 64, sprint1Percentage, COLOR_SPRINT)

    // Add percentage text or checkmark inside sprint bar (centered)
    if (sprint1Percentage >= 100) {
      // Draw checkmark centered in sprint 1 bar
      const checkX = Math.floor((sprintWidth - 7) / 2)
      drawCheckmark(pixels, checkX, 35)
    } else {
      const s1Text = `${Math.floor(sprint1Percentage)}%`
      const s1TextWidth = s1Text.length * 4 - 1
      const s1TextX = Math.floor((sprintWidth - s1TextWidth) / 2)
      const s1TextY = 35 // Middle of sprint bar
      drawText(pixels, s1Text, s1TextX, s1TextY, { r: 255, g: 255, b: 255 })
    }
  }

  // Sprint 2
  if (sprints.length >= 2) {
    const sprint2Percentage = sprints[1].progress?.percentage || 0
    const s2XStart = sprintWidth
    const s2XEnd = sprintWidth * 2

    // Draw "S2" label
    drawText(pixels, 'S2', s2XStart + 7, LABEL_ROW, { r: 255, g: 255, b: 255 })

    // Draw sprint bar
    fillVerticalBar(pixels, s2XStart, s2XEnd, 13, 64, sprint2Percentage, COLOR_SPRINT)

    // Add percentage text or checkmark inside sprint bar (centered)
    if (sprint2Percentage >= 100) {
      // Draw checkmark centered in sprint 2 bar
      const checkX = s2XStart + Math.floor((sprintWidth - 7) / 2)
      drawCheckmark(pixels, checkX, 35)
    } else {
      const s2Text = `${Math.floor(sprint2Percentage)}%`
      const s2TextWidth = s2Text.length * 4 - 1
      const s2TextX = s2XStart + Math.floor((sprintWidth - s2TextWidth) / 2)
      const s2TextY = 35
      drawText(pixels, s2Text, s2TextX, s2TextY, { r: 255, g: 255, b: 255 })
    }
  }

  // Sprint 3 slot (empty, darker to show it's available)
  const s3XStart = sprintWidth * 2
  const s3XEnd = 64
  // Draw empty slot with very dim color to show it's available
  for (let x = s3XStart; x < s3XEnd; x++) {
    for (let y = 13; y < 64; y++) {
      if (x >= 0 && x < 64 && y >= 0 && y < 64) {
        pixels[y][x] = { r: 10, g: 10, b: 10 } // Very dim gray
      }
    }
  }

  return pixels
}

export function generateUserStoryLayoutPixels(
  sprintData: GaugeData,
  userStories: GaugeData[]
): LEDPixel[][] {
  const pixels = createEmptyPixels()

  // Data for each line (sprint + all user stories)
  const lineData = [sprintData, ...(userStories || [])]

  // Layout constants - dynamic based on number of lines
  const totalLines = lineData.length
  const LINE_HEIGHT = Math.floor(64 / Math.max(totalLines, 1))
  const GAUGE_OUTLINE_COLOR = { r: 100, g: 100, b: 100 } // Gray
  const TEXT_COLOR = { r: 255, g: 255, b: 255 } // White

  // User story colors matching LED panel hardware (same as USER_STORY_COLORS in led_layout_renderer.py)
  const USER_STORY_COLORS = [
    { r: 0, g: 100, b: 255 },    // Blue
    { r: 255, g: 255, b: 0 },    // Yellow
    { r: 0, g: 255, b: 255 },    // Cyan
    { r: 255, g: 0, b: 255 },    // Magenta
    { r: 255, g: 128, b: 0 },    // Orange
    { r: 128, g: 255, b: 0 },    // Lime
    { r: 255, g: 0, b: 128 },    // Pink
    { r: 128, g: 0, b: 255 },    // Purple
  ]

  // Different colors per line (matching LED panel colors)
  const LINE_COLORS = [
    COLOR_SPRINT,      // Line 1 (Sprint): Green
    ...(userStories || []).map((_, i) => USER_STORY_COLORS[i % USER_STORY_COLORS.length])
  ]

  // Line labels (S1, U1, U2, U3, ...)
  const LINE_LABELS = ['S1', ...(userStories || []).map((_, i) => `U${i + 1}`)]

  // Render all lines
  for (let i = 0; i < lineData.length; i++) {
    const yStart = i * LINE_HEIGHT
    const yEnd = (i + 1) * LINE_HEIGHT
    const yCenter = yStart + Math.floor(LINE_HEIGHT / 2)
    const yText = yCenter - 2 // Adjust for 5px text height

    // Gauge dimensions (horizontally centered in available space)
    const gaugeYStart = yStart + 6  // Vertically center the gauge
    const gaugeYEnd = yEnd - 6

    if (lineData[i]) {
      const data = lineData[i]
      const percentage = data.percentage || 0
      const lineColor = LINE_COLORS[i]

      // 1. Draw label "S1", "U1", "U2" on left
      const label = LINE_LABELS[i]
      drawText(pixels, label, 2, yText, TEXT_COLOR)

      // 2. Draw gauge outline (middle section - 24px wide)
      drawOutlineRectangle(
        pixels,
        14,
        38,
        gaugeYStart,
        gaugeYEnd,
        GAUGE_OUTLINE_COLOR
      )

      // 3. Fill gauge based on percentage with line color
      fillHorizontalBar(
        pixels,
        15,  // Inside outline
        37,
        gaugeYStart + 1,
        gaugeYEnd - 1,
        percentage,
        lineColor
      )

      // 4. Draw percentage or checkmark on right
      if (percentage >= 100) {
        // Draw checkmark on right side (moved up 5 pixels)
        drawCheckmark(pixels, 40, yText - 6)
      } else {
        const pctText = `${Math.floor(percentage)}%`
        drawText(pixels, pctText, 40, yText, TEXT_COLOR)
      }
    } else {
      // No data - show empty slot
      const label = LINE_LABELS[i]
      drawText(pixels, label, 2, yText, TEXT_COLOR)

      // Draw empty gauge outline (24px wide)
      drawOutlineRectangle(
        pixels,
        14,
        38,
        gaugeYStart,
        gaugeYEnd,
        GAUGE_OUTLINE_COLOR
      )
    }
  }

  return pixels
}

export function generateHierarchyViewPixels(
  projectData: ProjectData,
  sprints: SprintData[]
): LEDPixel[][] {
  const pixels = createEmptyPixels()

  // Top horizontal project bar (6px tall)
  const PROJECT_BAR_HEIGHT = 6
  const projectPercentage = projectData.progress?.percentage || 0
  fillHorizontalBar(pixels, 0, 64, 0, PROJECT_BAR_HEIGHT, projectPercentage, COLOR_PROJECT)

  if (!sprints || sprints.length === 0) {
    return pixels
  }

  // Sprint rows (proportionally divided)
  const remainingHeight = 64 - PROJECT_BAR_HEIGHT
  const numSprints = sprints.length
  const sprintRowHeight = Math.floor(remainingHeight / numSprints)

  const SPRINT_BAR_WIDTH = 10
  const STORIES_SECTION_WIDTH = 64 - SPRINT_BAR_WIDTH

  for (let sprintIdx = 0; sprintIdx < sprints.length; sprintIdx++) {
    const sprint = sprints[sprintIdx]
    const rowYStart = PROJECT_BAR_HEIGHT + (sprintIdx * sprintRowHeight)
    const rowYEnd = Math.min(PROJECT_BAR_HEIGHT + ((sprintIdx + 1) * sprintRowHeight), 64)

    // Draw vertical sprint bar on left
    const sprintPercentage = sprint.progress?.percentage || 0
    fillVerticalBar(pixels, 0, SPRINT_BAR_WIDTH, rowYStart, rowYEnd, sprintPercentage, COLOR_SPRINT)

    // Draw user story bars on right
    const userStories = sprint.user_stories || []
    if (userStories.length > 0) {
      const numStories = userStories.length
      const storyBarWidth = Math.floor(STORIES_SECTION_WIDTH / numStories)

      for (let storyIdx = 0; storyIdx < numStories; storyIdx++) {
        const storyXStart = SPRINT_BAR_WIDTH + (storyIdx * storyBarWidth)
        const storyXEnd = Math.min(SPRINT_BAR_WIDTH + ((storyIdx + 1) * storyBarWidth), 64)

        const storyPercentage = userStories[storyIdx].progress?.percentage || 0
        fillVerticalBar(
          pixels,
          storyXStart,
          storyXEnd,
          rowYStart,
          rowYEnd,
          storyPercentage,
          COLOR_USER_STORY
        )
      }
    }
  }

  return pixels
}
