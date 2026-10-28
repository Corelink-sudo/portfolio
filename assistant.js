/* Jaguar portfolio helper. Answers common questions from the site content.
 * For live AI, configure a same-origin backend via CONFIG.assistantEndpoint.
 * The backend (not this file) selects the model and stores its API key.
 */
(() => {
  'use strict';
  const get = id => document.getElementById(id);
  const toggle = get('assistantToggle');
  const panel = get('assistantPanel');
  const input = get('assistantInput');
  const log = get('assistantLog');
  const send = get('assistantSend');
  const config = typeof CONFIG === 'undefined' ? {} : CONFIG;
  const live = Boolean(config.assistantEndpoint);
  const history = [];
  const REPLY_DELAY_MS = 5500;
  let busy = false;

  function message(role, text) {
    const bubble = document.createElement('div');
    bubble.className = 'assistant-message ' + role;
    const label = document.createElement('strong');
    label.textContent = role === 'user' ? 'You' : 'Jaguar';
    bubble.append(label, document.createTextNode(text));
    log.append(bubble);
    // Bound in-memory history and DOM size. Nothing is saved to localStorage.
    while (log.children.length > 60) log.firstElementChild.remove();
    log.scrollTop = log.scrollHeight;
    return bubble;
  }

  function typingIndicator() {
    const bubble = message('assistant', '');
    bubble.classList.add('is-typing');
    bubble.setAttribute('aria-label', 'Jaguar is preparing a reply');
    const dots = document.createElement('span');
    dots.className = 'assistant-typing-dots';
    dots.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < 3; i++) dots.append(document.createElement('span'));
    bubble.append(dots);
    log.scrollTop = log.scrollHeight;
    return bubble;
  }

  function close(restoreFocus = true) {
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    if (restoreFocus) toggle.focus({ preventScroll: true });
  }

  toggle.addEventListener('click', () => {
    if (!panel.hidden) return close();
    panel.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
    input.focus({ preventScroll: true });
  });
  get('assistantClose').addEventListener('click', () => close());
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) {
      event.preventDefault();
      close();
    }
  });
  // Do not cover the site's existing mobile menu or fullscreen video player.
  document.addEventListener('click', () => {
    if (!panel.hidden && (get('player').classList.contains('open') ||
        get('burger').getAttribute('aria-expanded') === 'true')) close(false);
  });

  function portfolioReply(question) {
    const q = question.toLowerCase().replace(/[’']/g, '').replace(/[^a-z0-9$]+/g, ' ').trim();
    const plans = Array.from(document.querySelectorAll('.price'));
    const selectedPlan = plans.find(card =>
      new RegExp('\\b' + card.querySelector('h3').textContent.toLowerCase() + '\\b').test(q)
    );
    if (selectedPlan) {
      return selectedPlan.querySelector('h3').textContent + ' — ' +
        selectedPlan.querySelector('.price-for').textContent + '\nStarting at ' +
        selectedPlan.querySelector('.amt').textContent.trim() + '\n' +
        Array.from(selectedPlan.querySelectorAll('li')).map(item => '• ' + item.textContent).join('\n') +
        '\nContact Jaguar to confirm the scope and final quote.';
    }
    if (/\b(price|prices|pricing|rate|rates|cost|budget|package|packages|charge|charges)\b|how much/.test(q)) {
      return 'Starting rates:\n' + plans.map(card =>
        card.querySelector('h3').textContent + ': ' + card.querySelector('.amt').textContent.trim()
      ).join('\n') + '\nAsk about Essential, Pro, or Signature for inclusions, or contact Jaguar for a tailored quote.';
    }
    if (/\b(contact|email|hire|book|booking|touch|available|availability)\b/.test(q)) {
      return 'You can reach Jaguar at ' + (config.email || 'the email in the Contact section') +
        '. Share your brief, footage length, target platforms, and deadline. Confirm availability and your final quote directly with Jaguar.';
    }
    if (/\b(process|workflow|turnaround|delivery|deadline|time|long)\b/.test(q)) {
      const steps = Array.from(document.querySelectorAll('.step h3')).map(el => el.textContent);
      return 'The workflow is ' + steps.join(' → ') +
        '. The Essential package lists a 3–5 day turnaround. Other timelines depend on the scope; contact Jaguar to confirm your deadline.';
    }
    if (/\b(tools|software|skills|premiere|resolve|effects)\b/.test(q)) {
      return 'Tools and skills listed in the portfolio: ' + (config.skills || []).join(', ') + '.';
    }
    if (/\b(service|services|edit|editing|color|colour|grading|sound|motion)\b|what (can you|do you) do/.test(q)) {
      return 'Jaguar offers video editing, color grading, motion graphics, and sound design for social content, YouTube, brands, music videos, and films. There are three service packages: Essential, Pro, and Signature. Ask about a package or starting rates to learn more.';
    }
    const project = (config.projects || []).find(item => q.includes(item.title.toLowerCase()));
    if (project) {
      return project.title + ' is listed in Selected Work under ' +
        ({ commercials: 'Commercials', youtube: 'YouTube', music: 'Music Videos', shorts: 'Short Films' }[project.cat] || project.cat) +
        '. Open its card in the portfolio to watch it.';
    }
    if (/\b(work|portfolio|project|projects|reel|video|videos|youtube)\b/.test(q)) {
      const projects = (config.projects || []).slice(0, 5).map(item => item.title);
      return 'Explore Selected Work and use the category filters, or open Watch Reel. Selected Work includes ' +
        projects.join(', ') + '. Ask about a title to find its category.';
    }
    if (/\b(social|socials|instagram|vimeo|linkedin)\b/.test(q)) {
      return 'You can find the social links in the Contact section: ' +
        (config.socials || []).map(item => item.name).join(', ') + '.';
    }
    if (/\b(ai|model|gpt|chatgpt)\b/.test(q)) {
      return 'I’m a built-in portfolio helper, not a connected AI model. I answer common questions using the information on this site.';
    }
    if (/who (are you|is jaguar)|about (you|jaguar)|your name/.test(q)) {
      return 'This is Jaguar’s video editing and color grading portfolio. I’m the portfolio helper, here to answer questions about the work, services, packages, workflow, and contact details.';
    }
    if (/\b(thanks|thank)\b/.test(q)) {
      return 'You’re welcome! Let me know if you have another question about Jaguar’s work or services.';
    }
    if (/\b(hi|hello|hey)\b/.test(q)) {
      return 'Hi! I can help you explore Jaguar’s services, starting rates, workflow, work, and contact details. What would you like to know?';
    }
    return 'I can help with Jaguar’s services, packages, starting rates, tools, workflow, selected work, and contact details. Try “What’s included in Pro?” or “How do I book?” For a question specific to your project, contact Jaguar directly.';
  }

  async function liveReply(question) {
    const endpoint = new URL(config.assistantEndpoint, location.href);
    if (endpoint.origin !== location.origin || !/^https?:$/.test(endpoint.protocol)) {
      throw new Error('A same-origin assistant backend is required.');
    }
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(endpoint.href, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ message: question, history: history.slice(-12) }),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error('Assistant request failed.');
      const data = await response.json();
      if (typeof data.reply !== 'string' || !data.reply.trim() || data.reply.length > 12000) {
        throw new Error('Invalid assistant response.');
      }
      return data.reply.trim();
    } finally {
      clearTimeout(timeout);
    }
  }

  async function ask(question) {
    question = question.trim();
    if (!question || question.length > 1000 || busy) return;
    busy = true;
    send.disabled = true;
    message('user', question);
    input.value = '';
    log.setAttribute('aria-busy', 'true');
    const pending = typingIndicator();
    try {
      // Fetch/generate in parallel with the animation; never flash an instant reply.
      // allSettled also avoids an unhandled rejection if the backend fails early.
      const [result] = await Promise.allSettled([
        Promise.resolve().then(() => live ? liveReply(question) : portfolioReply(question)),
        new Promise(resolve => setTimeout(resolve, REPLY_DELAY_MS)),
      ]);
      if (result.status === 'rejected') throw result.reason;
      const reply = result.value;
      pending.remove();
      message('assistant', reply);
      history.push({ role: 'user', content: question }, { role: 'assistant', content: reply });
      if (history.length > 12) history.splice(0, history.length - 12);
    } catch (error) {
      pending.remove();
      message('assistant', 'Sorry, the assistant could not respond. Please try again, or use the Contact section. Your message has not been sent to Jaguar as an inquiry.');
    } finally {
      busy = false;
      send.disabled = false;
      log.setAttribute('aria-busy', 'false');
      // Do not steal focus if the visitor closed the panel or moved elsewhere.
      if (!panel.hidden && document.activeElement === send) input.focus({ preventScroll: true });
    }
  }

  get('assistantForm').addEventListener('submit', event => {
    event.preventDefault();
    ask(input.value);
  });
  panel.querySelectorAll('[data-question]').forEach(button => {
    button.addEventListener('click', () => ask(button.dataset.question));
  });

  if (live) {
    get('assistantMode').textContent = 'AI backend mode';
    get('assistantPrivacy').textContent = 'Messages are sent to the site’s AI backend. Avoid sharing sensitive information. Replies may be inaccurate.';
  }
  message('assistant', 'Hi! I’m Jaguar’s portfolio helper. Ask me about services, starting rates, packages, workflow, or selected work. How can I help?');
  // Progressive enhancement: avoid displaying a dead button if JS is disabled.
  toggle.hidden = false;
})();
