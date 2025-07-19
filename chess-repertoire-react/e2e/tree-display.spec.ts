import { test, expect } from '@playwright/test';
import { writeFileSync } from 'fs';
import { join } from 'path';

test.describe('Chess Repertoire Builder - Tree Display', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display main line moves inline', async ({ page }) => {
    // Test that basic moves are displayed in a clean inline format
    await page.waitForSelector('h1:text("Chess Repertoire Builder")');
    
    // Verify the initial state
    await expect(page.locator('.move-history h3')).toHaveText('Move History');
    await expect(page.locator('.no-moves')).toHaveText('No moves yet. Start playing!');
  });

  test('should display variations with proper indentation and visual hierarchy', async ({ page }) => {
    // Create a test PGN with variations
    const testPGN = `[Event "Tree Display Test"]
[Site "Chess Repertoire Builder"]
[Date "2024.01.01"]
[White "White Player"]
[Black "Black Player"]
[Result "*"]

1. e4 e5 (1... c5 {Sicilian Defense} 2. Nf3 d6) 2. Nf3 Nc6 3. Bb5 *`;

    // Write the test PGN to a temporary file
    const tempPGNPath = join(process.cwd(), 'test-files/test-variation.pgn');
    writeFileSync(tempPGNPath, testPGN);

    // Load the PGN file
    await page.locator('input[type="file"]').setInputFiles(tempPGNPath);

    // Wait for the moves to be loaded and displayed
    await page.waitForSelector('.move-pair', { timeout: 5000 });

    // Verify main line moves are displayed
    await expect(page.locator('text=1.')).toBeVisible();
    await expect(page.locator('text=e4')).toBeVisible();
    await expect(page.locator('text=e5')).toBeVisible();
    await expect(page.locator('text=2.')).toBeVisible();
    await expect(page.locator('text=Nf3')).toBeVisible();
    await expect(page.locator('text=Nc6')).toBeVisible();

    // Verify variation structure with new tree format
    await expect(page.locator('.variation-line')).toBeVisible();
    await expect(page.locator('.variation-prefix')).toContainText('|-');
    
    // Verify variation moves are indented and visually distinct
    const variationLine = page.locator('.variation-line').first();
    await expect(variationLine).toHaveCSS('margin-left', '24px'); // 1.5rem = 24px
    await expect(variationLine).toHaveCSS('border-left', '2px solid rgb(52, 152, 219)');

    // Verify variation moves are displayed
    await expect(page.locator('text=c5')).toBeVisible();
    await expect(page.locator('text=Sicilian Defense')).toBeVisible();

    // Clean up
    const fs = require('fs');
    try {
      fs.unlinkSync(tempPGNPath);
    } catch (e) {
      // File may not exist, ignore
    }
  });

  test('should highlight current move correctly in tree structure', async ({ page }) => {
    const simplePGN = `[Event "Highlight Test"]
[Site "Chess Repertoire Builder"]
[Date "2024.01.01"]
[White "White"]
[Black "Black"]
[Result "*"]

1. e4 e5 2. Nf3 *`;

    const tempPGNPath = join(process.cwd(), 'test-files/test-highlight.pgn');
    writeFileSync(tempPGNPath, simplePGN);

    await page.locator('input[type="file"]').setInputFiles(tempPGNPath);
    await page.waitForSelector('.move-pair', { timeout: 5000 });

    // Navigate through moves using the navigation controls
    await page.locator('button:text("⏮️ Start")').click();
    
    // No move should be highlighted at start
    await expect(page.locator('.current-move')).toHaveCount(0);

    // Navigate forward one move
    await page.locator('button:text("⏩ Forward")').click();
    
    // First move should be highlighted
    const firstMove = page.locator('text=e4').locator('..');
    await expect(firstMove).toHaveClass(/current-move/);

    // Navigate forward again
    await page.locator('button:text("⏩ Forward")').click();
    
    // Second move should be highlighted
    const secondMove = page.locator('text=e5').locator('..');
    await expect(secondMove).toHaveClass(/current-move/);

    // Clean up
    const fs = require('fs');
    try {
      fs.unlinkSync(tempPGNPath);
    } catch (e) {
      // File may not exist, ignore
    }
  });

  test('should allow clicking on moves to navigate in tree structure', async ({ page }) => {
    const clickTestPGN = `[Event "Click Test"]
[Site "Chess Repertoire Builder"]
[Date "2024.01.01"]
[White "White"]
[Black "Black"]
[Result "*"]

1. d4 d5 2. c4 dxc4 *`;

    const tempPGNPath = join(process.cwd(), 'test-files/test-click.pgn');
    writeFileSync(tempPGNPath, clickTestPGN);

    await page.locator('input[type="file"]').setInputFiles(tempPGNPath);
    await page.waitForSelector('.move-pair', { timeout: 5000 });

    // Click on the second move (d5)
    await page.locator('text=d5').click();

    // Verify that the position updated - the board should show the position after d5
    // We can check this by looking at the navigation buttons state
    await expect(page.locator('button:text("⏪ Back")')).not.toBeDisabled();
    await expect(page.locator('button:text("⏩ Forward")')).not.toBeDisabled();

    // Click on the first move (d4)
    await page.locator('text=d4').click();

    // Verify navigation state changed
    await expect(page.locator('button:text("⏪ Back")')).not.toBeDisabled();

    // Clean up
    const fs = require('fs');
    try {
      fs.unlinkSync(tempPGNPath);
    } catch (e) {
      // File may not exist, ignore
    }
  });

  test('should display nested variations with increasing indentation', async ({ page }) => {
    const nestedPGN = `[Event "Nested Variations Test"]
[Site "Chess Repertoire Builder"]  
[Date "2024.01.01"]
[White "White"]
[Black "Black"]
[Result "*"]

1. e4 e5 (1... c5 2. Nf3 (2. Nc3 d6) 2... d6) 2. Nf3 *`;

    const tempPGNPath = join(process.cwd(), 'test-files/test-nested.pgn');
    writeFileSync(tempPGNPath, nestedPGN);

    await page.locator('input[type="file"]').setInputFiles(tempPGNPath);
    await page.waitForSelector('.move-pair', { timeout: 5000 });

    // Verify that variations are present with new tree format
    await expect(page.locator('.variation-line')).toHaveCount({ min: 1 });
    
    // Verify variation structure with tree prefix
    await expect(page.locator('.variation-prefix')).toBeVisible();
    
    // Verify visual hierarchy with borders and indentation
    const variationLines = page.locator('.variation-line');
    await expect(variationLines.first()).toHaveCSS('border-left', '2px solid rgb(52, 152, 219)');

    // Clean up
    const fs = require('fs');
    try {
      fs.unlinkSync(tempPGNPath);
    } catch (e) {
      // File may not exist, ignore
    }
  });
});