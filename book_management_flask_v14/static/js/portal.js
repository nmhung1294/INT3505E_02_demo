// Portal JavaScript

// Test webhook function
async function testWebhook() {
    try {
        const response = await fetch('/webhooks/test', {
            method: 'POST'
        });
        const data = await response.json();
        alert('Webhook test sent! Check your configured webhook URLs.');
    } catch (error) {
        alert('Error sending test webhook: ' + error.message);
    }
}

// Download Postman collection
function downloadPostman() {
    window.location.href = '/postman_collection_v10.json';
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Highlight active section in navigation
const observerOptions = {
    root: null,
    rootMargin: '-20% 0px -80% 0px',
    threshold: 0
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const id = entry.target.getAttribute('id');
            document.querySelectorAll('.nav-links a').forEach(link => {
                link.style.color = '';
                if (link.getAttribute('href') === `#${id}`) {
                    link.style.color = 'var(--primary)';
                    link.style.fontWeight = '600';
                } else {
                    link.style.fontWeight = '400';
                }
            });
        }
    });
}, observerOptions);

// Observe all sections
document.querySelectorAll('.section[id]').forEach(section => {
    observer.observe(section);
});

// Copy code to clipboard
document.querySelectorAll('pre code').forEach(block => {
    block.addEventListener('click', function() {
        const text = this.textContent;
        navigator.clipboard.writeText(text).then(() => {
            const originalBg = this.parentElement.style.background;
            this.parentElement.style.background = '#d1fae5';
            setTimeout(() => {
                this.parentElement.style.background = originalBg;
            }, 300);
        });
    });
    
    // Add cursor pointer to indicate clickable
    block.style.cursor = 'pointer';
    block.title = 'Click to copy';
});
