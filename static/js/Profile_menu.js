document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');

    function showSection(sectionId) {
        contentSections.forEach(section => {
            section.classList.add('hidden');
        });
        document.getElementById(sectionId).classList.remove('hidden');
    }

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('data-target');
            showSection(target);
            navLinks.forEach(l => l.classList.remove('text-indigo-600', 'font-medium'));
            this.classList.add('text-indigo-600', 'font-medium');
        });
    });

    // 默認顯示個人資料頁面
    showSection('personal-info');
    navLinks[0].classList.add('text-indigo-600', 'font-medium');
});