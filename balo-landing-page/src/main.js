// ═══════════════════════════════════════════
// Balo Landing Page - Client Interactivity
// ═══════════════════════════════════════════

import './style.css';

document.addEventListener('DOMContentLoaded', () => {
  // Mobile navigation drawer toggle
  const mobileToggle = document.getElementById('mobileToggle');
  const navLinks = document.getElementById('navLinks');

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
    });

    // Close menu when clicking any nav link
    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('active');
      });
    });
  }

  // FAQ Accordions
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach(item => {
    const questionBtn = item.querySelector('.faq-question');
    if (questionBtn) {
      questionBtn.addEventListener('click', () => {
        const isActive = item.classList.contains('active');
        // Close all other items
        faqItems.forEach(otherItem => otherItem.classList.remove('active'));
        // Toggle clicked
        if (!isActive) {
          item.classList.add('active');
        }
      });
    }
  });

  // CTA Click handlers (smooth scroll or feedback)
  document.querySelectorAll('[data-cta]').forEach(cta => {
    cta.addEventListener('click', (e) => {
      const action = cta.getAttribute('data-cta');
      if (action === 'download') {
        // Log intent or guide user
        console.log('[Balo] CTA clicked: Download Android APK');
      }
    });
  });
});
