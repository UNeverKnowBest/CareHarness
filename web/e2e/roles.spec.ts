import { expect, test } from "@playwright/test";

test("role-separated English and Chinese research surfaces", async ({ page }) => {
  await page.goto("/en/participant");
  await expect(page.getByText("Adult synthetic role-play research only")).toBeVisible();
  await expect(page.getByText("Participant studio")).toBeVisible();
  await page.goto("/en/reviewer");
  await expect(page.getByText("Evidence before action.")).toBeVisible();
  await expect(page.getByText(/not staffed care/)).toBeVisible();
  await page.goto("/en/admin");
  await expect(page.getByText("Capabilities stay bounded.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Required" }).first()).toBeDisabled();
  await page.goto("/zh-CN/participant");
  await expect(page.getByText("仅限成人合成角色扮演研究")).toBeVisible();
  await expect(page.getByText(/不会联系临床人员、急救服务、家人或政府部门/)).toBeVisible();
});
