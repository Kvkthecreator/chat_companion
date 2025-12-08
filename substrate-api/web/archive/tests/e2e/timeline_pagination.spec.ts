import { test, expect } from '@playwright/test';
const basketId = process.env.TEST_BASKET_ID;
test.skip(!basketId, 'requires TEST_BASKET_ID to run');

test('timeline paginates with last_cursor', async ({ page }) => {
  await page.goto(`/baskets/${basketId}/timeline`);

  const items = page.locator('[data-test=timeline-item]');
  await expect(items.first()).toBeVisible();

  const loadMore = page.getByRole('button', { name: /load more/i });
  await loadMore.click();

  await expect(items).toHaveCountGreaterThan(1);
});
