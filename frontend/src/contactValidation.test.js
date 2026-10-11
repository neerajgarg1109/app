import { contactEmailError, contactNameError, contactPhoneError } from "./contactValidation";

describe("contact validation", () => {
  test.each([
    "Neeraj Garg", "A P J Abdul Kalam", "Mary D'Souza", "Anne-Marie", "V. Iyer", "आरव शर्मा",
  ])("accepts a legitimate name: %s", (name) => expect(contactNameError(name)).toBe(""));

  test.each([
    ["", "Enter your full name."], ["A", "Enter your full name."], ["Neeraj123", "Use letters only"],
    ["asdf", "Enter your real name."], ["aaaaaa", "Enter your real name."], ["@@@", "Enter your full name."],
  ])("rejects invalid name %s", (name, message) => expect(contactNameError(name)).toContain(message));

  test.each(["9876543210", "+91 98765 43210", "91-98765-43210", "(98765) 43210"])(
    "accepts an Indian mobile: %s", (phone) => expect(contactPhoneError(phone)).toBe("")
  );

  test.each(["", "12345", "5876543210", "+1 9876543210", "98765432100", "abcdefghij"])(
    "rejects invalid mobile %s", (phone) => expect(contactPhoneError(phone)).toContain("valid 10-digit")
  );

  test.each(["person@example.com", "first.last+cards@sub.example.co.in"])(
    "accepts a valid email: %s", (email) => expect(contactEmailError(email)).toBe("")
  );

  test.each(["", "hello@", "hello@example", "a..b@example.com", "@example.com", "a@-example.com"])(
    "rejects invalid email %s", (email) => expect(contactEmailError(email)).toContain("valid email")
  );
});
