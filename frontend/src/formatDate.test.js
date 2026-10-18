import { formatCustomerDate } from "./formatDate";

test("formats catalogue dates for Indian readers", () => {
  expect(formatCustomerDate("2026-10-09")).toBe("9 Oct 2026");
  expect(formatCustomerDate("2026-10-09T14:30:00Z")).toBe("9 Oct 2026");
});

test("keeps missing and non-standard dates safe", () => {
  expect(formatCustomerDate()).toBe("");
  expect(formatCustomerDate("date pending")).toBe("date pending");
});
