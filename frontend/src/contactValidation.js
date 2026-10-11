export function contactNameError(value) {
  const clean = value.trim().replace(/\s+/g, " ");
  const letters = Array.from(clean).filter((char) => /\p{L}/u.test(char));
  const compact = letters.join("").toLocaleLowerCase();
  if (clean.length < 2 || clean.length > 80 || letters.length < 2) return "Enter your full name.";
  if (!/^[\p{L}\p{M} .'-]+$/u.test(clean)) return "Use letters only—no numbers or symbols.";
  if (["asdf", "qwerty", "zxcv", "test", "unknown", "none", "random"].includes(compact) || /(.)\1{3,}/u.test(compact)) return "Enter your real name.";
  return "";
}

export function contactPhoneError(value) {
  let digits = value.replace(/[\s()\-]/g, "");
  if (digits.startsWith("+91")) digits = digits.slice(3);
  else if (digits.startsWith("91") && digits.length === 12) digits = digits.slice(2);
  return /^[6-9]\d{9}$/.test(digits) ? "" : "Enter a valid 10-digit Indian mobile number.";
}

export function contactEmailError(value) {
  const clean = value.trim();
  if (clean.length > 254 || clean.includes("..") || !/^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$/i.test(clean)) return "Enter a valid email address.";
  return "";
}
