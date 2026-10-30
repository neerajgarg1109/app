/* Keep Admin-published footer links consistent with the app, with a complete offline fallback. */
(() => {
  const footer = document.querySelector('.customer-footer');
  if (!footer) return;
  const origin = footer.dataset.publicOrigin;
  const destination = value => {
    if (typeof value !== 'string') throw new Error('Invalid footer destination');
    if (/^https:\/\//.test(value)) return value;
    if (!value.startsWith('/') || value.startsWith('//')) throw new Error('Invalid footer destination');
    const base = new URL(origin).pathname.replace(/\/$/, '');
    const path = base && value.startsWith(base + '/') ? value.slice(base.length) : value;
    const staticRoutes = {'/cards': '/catalog/', '/cards?mode=compare': '/compare/', '/calculator': '/calculator/', '/updates': '/guides/new-credit-cards/', '/restricted-cards': '/guides/invite-only-credit-cards/'};
    if (staticRoutes[path]) return origin + staticRoutes[path];
    const spa = path === '/' || ['/cards', '/updates', '/restricted-cards', '/calculator', '/wallet-optimizer', '/alerts', '/help/issuers'].some(route => path.startsWith(route));
    return origin + (spa ? '/#' + path : path);
  };
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  fetch(footer.dataset.contentUrl, {signal: controller.signal}).then(response => {
    if (!response.ok) throw new Error('Footer unavailable');
    return response.json();
  }).then(data => {
    if (!Array.isArray(data.footer_groups) || !data.footer_groups.length) return;
    const sections = data.footer_groups.map((group, index) => {
      const section = document.createElement('section');
      const heading = document.createElement('h2');
      heading.id = 'footer-group-' + index;
      heading.textContent = group.title;
      section.setAttribute('aria-labelledby', heading.id);
      const list = document.createElement('ul');
      group.links.forEach(link => {
        const item = document.createElement('li');
        const anchor = document.createElement('a');
        anchor.href = destination(link.url);
        anchor.textContent = link.label;
        item.append(anchor); list.append(item);
      });
      section.append(heading, list); return section;
    });
    const grid = footer.querySelector('.customer-footer-grid');
    grid.querySelectorAll('section').forEach(section => section.remove());
    grid.append(...sections);
  }).catch(() => {}).finally(() => clearTimeout(timeout));
})();
