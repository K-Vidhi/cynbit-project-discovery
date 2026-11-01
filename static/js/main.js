/* Cynbit project discovery: navigation, multi-step brief form, small helpers. */
(function () {
  'use strict';

  /* ---------- navigation (runs on every page) ---------- */
  var toggle = document.querySelector('.menu-toggle');
  var nav = document.getElementById('primaryNav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }
  document.querySelectorAll('.nav-item.has-menu > .nav-link').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var item = btn.parentElement;
      var open = item.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(open));
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.nav-item.open').forEach(function (i) { i.classList.remove('open'); });
      if (nav) nav.classList.remove('open');
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
    }
  });

  /* ---------- copy reference button (thank-you page) ---------- */
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var target = document.querySelector(btn.getAttribute('data-copy'));
      if (!target) return;
      var text = target.textContent.trim();
      var done = function () { btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = 'Copy reference'; }, 1800); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, done);
      } else { done(); }
    });
  });

  /* ---------- multi-step inquiry form ---------- */
  var form = document.getElementById('inquiryForm');
  if (!form) return;

  var steps = Array.prototype.slice.call(form.querySelectorAll('.form-step'));
  var stepperItems = Array.prototype.slice.call(form.querySelectorAll('#stepper li'));
  var bar = document.getElementById('progressBar');
  var current = 0;

  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var PHONE_RE = /^\+?[0-9()\-\s]{7,20}$/;

  var PROMPTS = {
    software: ['Software engineering', 'Who will use it, on which devices, and which existing systems must it connect to? Mention the features that matter most in the first release.'],
    ai: ['AI automation', 'Which manual process or repetitive task do you want to automate? Tell us how much volume it handles and what data or tools it relies on today.'],
    cloud: ['Cloud infrastructure', 'What are you running today, where is it hosted, and what is the pain: cost, performance, security or scaling? Note any compliance needs.'],
    marketing: ['Digital marketing & SEO', 'Which audience and markets are you targeting, what are your current channels, and what result do you want in the next 6 months?'],
    other: ['Not sure yet', 'Describe the problem in your own words. We will help you shape the right solution and the right team.']
  };
  var DEFAULT_PROMPT = ['Let\u2019s shape the brief.', 'Choose a capability to see questions tailored to it.'];

  function errorEl(name) { return form.querySelector('[data-error-for="' + name + '"]'); }
  function wrapperOf(name) {
    var el = errorEl(name);
    return el ? (el.closest('.field') || el.closest('fieldset')) : null;
  }
  function setError(name, message) {
    var el = errorEl(name);
    if (!el) return;
    el.textContent = message || '';
    var wrap = wrapperOf(name);
    if (wrap) wrap.classList.toggle('has-error', Boolean(message));
  }
  function clearError(name) { setError(name, ''); }

  function validateField(name) {
    var value, field;
    switch (name) {
      case 'name':
        value = form.elements.name.value.trim();
        if (!value) return 'Please tell us your name.';
        if (value.length < 2) return 'Please enter your full name.';
        return '';
      case 'email':
        value = form.elements.email.value.trim();
        if (!value) return 'We need an email address to reply to you.';
        if (!EMAIL_RE.test(value)) return 'Enter a valid email address, for example name@company.com.';
        return '';
      case 'phone':
        value = form.elements.phone.value.trim();
        if (value && !PHONE_RE.test(value)) return 'Enter a valid phone number, for example +91 98765 43210.';
        return '';
      case 'service':
        if (!form.querySelector('input[name="service"]:checked')) return 'Please choose the closest area of expertise.';
        return '';
      case 'description':
        value = form.elements.description.value.trim();
        if (!value) return 'Please describe your project.';
        if (value.length < 20) return 'Please write at least 20 characters so the team can understand your project.';
        if (value.length > 2000) return 'Please keep the overview under 2000 characters.';
        return '';
      case 'consent':
        field = form.elements.consent;
        return field.checked ? '' : 'Please confirm so we can store your brief and contact you.';
      default:
        return '';
    }
  }

  var FIELDS_BY_STEP = [['name', 'email', 'phone'], ['service'], ['description', 'consent']];

  function validateStep(index) {
    var firstInvalid = null;
    FIELDS_BY_STEP[index].forEach(function (name) {
      var message = validateField(name);
      setError(name, message);
      if (message && !firstInvalid) firstInvalid = name;
    });
    if (firstInvalid) {
      var target = form.elements[firstInvalid];
      if (target && target.length && target.item) { target = form.querySelector('input[name="service"]'); }
      if (target && target.focus) target.focus();
      return false;
    }
    return true;
  }

  function show(index) {
    current = Math.max(0, Math.min(steps.length - 1, index));
    steps.forEach(function (s, i) { s.classList.toggle('is-active', i === current); });
    stepperItems.forEach(function (li, i) {
      li.classList.toggle('is-current', i === current);
      li.classList.toggle('is-done', i < current);
      var b = li.querySelector('button');
      if (b) { if (i === current) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current'); }
    });
    if (bar) bar.style.width = (((current + 1) / steps.length) * 100) + '%';
  }

  function scrollToForm() {
    var top = form.getBoundingClientRect().top + window.pageYOffset - 110;
    if (window.scrollTo) window.scrollTo({ top: top, behavior: 'smooth' });
  }

  form.querySelectorAll('.next').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (validateStep(current)) { show(current + 1); scrollToForm(); }
    });
  });
  form.querySelectorAll('.prev').forEach(function (btn) {
    btn.addEventListener('click', function () { show(current - 1); scrollToForm(); });
  });
  stepperItems.forEach(function (li) {
    var b = li.querySelector('button');
    if (!b) return;
    b.addEventListener('click', function () {
      var target = parseInt(b.getAttribute('data-goto'), 10);
      if (isNaN(target)) return;
      // Going forward requires every earlier step to be valid; going back is always allowed.
      if (target > current) {
        for (var i = current; i < target; i++) { if (!validateStep(i)) { show(i); return; } }
      }
      show(target);
    });
  });

  /* clear an error as soon as the visitor fixes the field */
  ['name', 'email', 'phone', 'description'].forEach(function (name) {
    var el = form.elements[name];
    if (!el) return;
    el.addEventListener('input', function () {
      if (errorEl(name) && errorEl(name).textContent) setError(name, validateField(name));
    });
    el.addEventListener('blur', function () { if (el.value.trim()) setError(name, validateField(name)); });
  });
  form.querySelectorAll('input[name="service"]').forEach(function (radio) {
    radio.addEventListener('change', function () { clearError('service'); updatePrompt(); });
  });
  if (form.elements.consent) form.elements.consent.addEventListener('change', function () { clearError('consent'); });

  /* service-specific prompt */
  var promptBox = document.getElementById('servicePrompt');
  function updatePrompt() {
    if (!promptBox) return;
    var checked = form.querySelector('input[name="service"]:checked');
    var data = checked && PROMPTS[checked.value] ? PROMPTS[checked.value] : DEFAULT_PROMPT;
    promptBox.innerHTML = '';
    var strong = document.createElement('strong');
    var p = document.createElement('p');
    strong.textContent = data[0];
    p.textContent = data[1];
    promptBox.appendChild(strong);
    promptBox.appendChild(p);
    var req = form.elements.requirements;
    if (req && checked && PROMPTS[checked.value]) req.placeholder = data[1];
  }
  updatePrompt();

  /* character counter */
  var desc = form.elements.description;
  var counter = document.getElementById('descCount');
  function updateCount() { if (counter && desc) counter.textContent = desc.value.length + ' / 2000'; }
  if (desc) { desc.addEventListener('input', updateCount); updateCount(); }

  /* final submit: validate every step, jump to the first one with a problem */
  form.addEventListener('submit', function (e) {
    for (var i = 0; i < steps.length; i++) {
      if (!validateStep(i)) {
        e.preventDefault();
        show(i);
        scrollToForm();
        return;
      }
    }
    var submit = document.getElementById('submitBtn');
    if (submit) { submit.disabled = true; submit.firstChild.textContent = 'Sending\u2026 '; }
  });

  /* restore the button if the visitor returns with the browser's Back button */
  window.addEventListener('pageshow', function () {
    var submit = document.getElementById('submitBtn');
    if (submit && submit.disabled) { submit.disabled = false; submit.firstChild.textContent = 'Submit project brief '; }
  });

  /* after a server-side error, open the first step that contains one */
  var firstWithError = steps.findIndex(function (s) { return s.hasAttribute('data-has-error'); });
  show(firstWithError >= 0 ? firstWithError : 0);
  if (firstWithError >= 0) {
    var firstMsg = form.querySelector('.field-error:not(:empty)');
    if (firstMsg) { setTimeout(function () { scrollToForm(); }, 50); }
  }
})();
