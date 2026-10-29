/* Only the spending scenario is enhanced; comparison content is build-time HTML. */
(function () {
  function estimate(model, monthly, kind, membership) {
    const rule = model.rules[kind];
    const amount = membership === 'first' ? model.joiningFee : model.annualFee;
    const waived = membership === 'renewal' && model.waiver != null && monthly * 12 >= model.waiver;
    const fee = amount == null ? null : Math.round((waived ? 0 : amount * 1.18) * 100) / 100;
    let gross = null;
    if (rule) {
      const months = rule[2] || 1;
      const raw = monthly * months * rule[0];
      gross = Math.round((rule[1] == null ? raw : Math.min(raw, rule[1])) * (12 / months) * 100) / 100;
    }
    return { gross, fee, net: gross == null || fee == null ? null : Math.round((gross - fee) * 100) / 100 };
  }
  // Also exercised directly in the Node arithmetic regression checks.
  if (typeof module !== 'undefined') module.exports = { estimate };
  if (typeof document === "undefined") return;
  const root = document.querySelector('[data-comparison-calculator]');
  if (!root) return;
  const models = JSON.parse(document.getElementById('comparison-models').textContent);
  const spend = document.getElementById('monthly-spend');
  const category = document.getElementById('spend-category');
  const year = document.getElementById('fee-year');
  const money = value => value == null ? 'Not estimated' : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value);
  function update() {
    const monthly = Math.max(10000, Math.min(100000, Number(spend.value) || 20000));
    document.getElementById('spend-output').textContent = money(monthly);
    const values = models.map(model => {
      const value = estimate(model, monthly, category.value, year.value);
      const box = root.querySelector('[data-result="' + model.id + '"]');
      ['gross', 'fee', 'net'].forEach(key => { box.querySelector('[data-value="' + key + '"]').textContent = money(value[key]); });
      return value;
    });
    const badge = document.getElementById('calculator-winner');
    badge.replaceChildren();
    if (values.some(value => value.net == null)) {
      badge.textContent = 'An input is not sufficiently verified for both cards in this scenario. No winner is estimated.';
      return;
    }
    const delta = Math.abs(values[0].net - values[1].net);
    if (delta < .01) { badge.textContent = 'Same estimated net value in this scenario. Compare the conditions and reward currency.'; return; }
    const winner = models[values[0].net > values[1].net ? 0 : 1];
    const text = document.createElement('p');
    text.textContent = '+' + money(delta) + '/yr estimated net-value difference with ' + winner.name + ' under these assumptions.';
    badge.appendChild(text);
    const link = document.createElement('a');
    link.href = winner.apply; link.className = 'cta'; link.target = '_blank'; link.rel = 'sponsored nofollow noopener';
    link.textContent = 'Apply for ' + winner.name + ' →'; badge.appendChild(link);
  }
  [spend, category, year].forEach(input => input.addEventListener('input', update));
  update();
})();
