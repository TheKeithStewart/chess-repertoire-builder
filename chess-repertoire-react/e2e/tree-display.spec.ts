import { test, expect } from "@playwright/test";
import { writeFileSync, unlinkSync, existsSync, mkdirSync } from "fs";
import { join } from "path";

// Make sure test-files directory exists
const testFilesDir = join(process.cwd(), "test-files");
if (!existsSync(testFilesDir)) {
  mkdirSync(testFilesDir);
}

test.describe("Chess Repertoire Builder - Tree Display", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should display no moves yet", async ({ page }) => {
    // Test that basic moves are displayed in a clean inline format
    await page.waitForSelector('h1:text("Chess Repertoire Builder")');

    // Verify the initial state
    await expect(page.locator(".move-history h3")).toHaveText("Move History");
    await expect(page.locator(".no-moves")).toHaveText(
      "No moves yet. Start playing!"
    );
  });

  test("should display variations with proper indentation and visual hierarchy", async ({
    page,
  }) => {
    // Create a test PGN with variations
    const testPGN = `[Event "Tree Display Test"]
[Site "Chess Repertoire Builder"]
[Date "2024.01.01"]
[White "White Player"]
[Black "Black Player"]
[Result "*"]

1. e4 e5 (1... c5 {Sicilian Defense} 2. Nf3 d6) 2. Nf3 Nc6 3. Bb5 *`;

    // Write the test PGN to a temporary file
    const tempPGNPath = join(process.cwd(), "test-files/test-variation.pgn");
    writeFileSync(tempPGNPath, testPGN);

    // Load the PGN file
    await page.locator('input[type="file"]').setInputFiles(tempPGNPath);

    // Wait for the moves to be loaded and displayed
    await page.waitForTimeout(1000);

    // Verify main line moves are displayed
    await expect(page.locator(".move-number-label").first()).toHaveText("1.");
    await expect(
      page.locator(".move-san").filter({ hasText: "e4" }).first()
    ).toBeVisible();
    await expect(
      page.locator(".move-san").filter({ hasText: "e5" }).first()
    ).toBeVisible();

    // Verify variation structure with tree-like format
    await expect(page.locator(".variation-line")).toBeVisible();
    await expect(page.locator(".variation-prefix")).toContainText("|-");

    // Verify variation moves are indented
    const variationLine = page.locator(".variation-line").first();
    await expect(variationLine).toHaveCSS(
      "border-left",
      "2px solid rgb(52, 152, 219)"
    );

    // Clean up
    if (existsSync(tempPGNPath)) {
      unlinkSync(tempPGNPath);
    }
  });

  test("should highlight current move correctly in tree structure", async ({
    page,
  }) => {
    const simplePGN = `[Event "Highlight Test"]
[Site "Chess Repertoire Builder"]
[Date "2024.01.01"]
[White "White"]
[Black "Black"]
[Result "*"]

1. e4 e5 2. Nf3 *`;

    const tempPGNPath = join(process.cwd(), "test-files/test-highlight.pgn");
    writeFileSync(tempPGNPath, simplePGN);

    await page.locator('input[type="file"]').setInputFiles(tempPGNPath);
    await page.waitForTimeout(1000);

    // Navigate through moves using the navigation controls
    await page.locator('button:text("⏮️ Start")').click();

    // No move should be highlighted at start
    await expect(page.locator(".current-move")).toHaveCount(0);

    // Navigate forward one move
    await page.locator('button:text("⏩ Forward")').click();

    // First move should be highlighted
    const firstMove = page.locator("text=e4").locator("..");
    await expect(firstMove).toHaveClass(/current-move/);

    // Navigate forward again
    await page.locator('button:text("⏩ Forward")').click();

    // Second move should be highlighted
    const secondMove = page.locator("text=e5").locator("..");
    await expect(secondMove).toHaveClass(/current-move/);

    // Clean up
    if (existsSync(tempPGNPath)) {
      unlinkSync(tempPGNPath);
    }
  });

  test("should allow clicking on moves to navigate in tree structure", async ({
    page,
  }) => {
    const clickTestPGN = `[Event "Click Test"]
[Site "Chess Repertoire Builder"]
[Date "2024.01.01"]
[White "White"]
[Black "Black"]
[Result "*"]

1. d4 d5 2. c4 dxc4 *`;

    const tempPGNPath = join(process.cwd(), "test-files/test-click.pgn");
    writeFileSync(tempPGNPath, clickTestPGN);

    await page.locator('input[type="file"]').setInputFiles(tempPGNPath);
    await page.waitForTimeout(1000); // Give time for the PGN to load

    // Click on the second move (d5)
    await page.locator("text=d5").click();
    await page.waitForTimeout(500); // Give time for the board to update

    // Verify that the position updated - check the navigation buttons state
    await expect(page.locator('button:text("⏪ Back")')).not.toBeDisabled();
    await expect(page.locator('button:text("⏩ Forward")')).not.toBeDisabled();

    // Verify the current move is highlighted
    await expect(page.locator("text=d5").locator("..")).toHaveClass(
      /current-move/
    );

    // Click on the first move (d4)
    await page.locator("text=d4").click();
    await page.waitForTimeout(500); // Give time for the board to update

    // Verify the new current move is highlighted
    await expect(page.locator("text=d4").locator("..")).toHaveClass(
      /current-move/
    );

    // Clean up
    if (existsSync(tempPGNPath)) {
      unlinkSync(tempPGNPath);
    }
  });});
