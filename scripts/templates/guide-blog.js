(() => {
  const search = document.getElementById('guide-search');
  const filters = [...document.querySelectorAll('[data-filter]')];
  const articles = [...document.querySelectorAll('[data-topic]')];
  const status = document.getElementById('result-count');
  let topic = 'all';
  function update() {
    const query = search.value.trim().toLocaleLowerCase();
    let count = 0;
    articles.forEach(article => {
      const visible = (topic === 'all' || article.dataset.topic === topic) && article.dataset.search.toLocaleLowerCase().includes(query);
      article.hidden = !visible;
      if (visible) count++;
    });
    filters.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === topic)));
    status.textContent = `${count} ${count === 1 ? 'guide' : 'guides'} ${query || topic !== 'all' ? 'found' : 'to explore'}`;
    document.getElementById('no-results').hidden = count !== 0;
  }
  search.addEventListener('input', update);
  filters.forEach(button => button.addEventListener('click', () => { topic = button.dataset.filter; update(); }));
  document.getElementById('reset-search').addEventListener('click', () => { search.value = ''; topic = 'all'; update(); search.focus(); });
})();
