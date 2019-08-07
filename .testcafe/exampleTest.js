import { Selector } from "testcafe";

fixture("Example test").page("http://localhost:8000/dashboard/next");

test("User can log in", async t => {
  await t
    .typeText('[name="email"]', "admin@example.com")
    .typeText('[name="password"]', "admin")
    .click('[type="submit"]');

  const header = await Selector('[data-tc="home-header"]').exists;
  await t.expect(header).ok();
});
