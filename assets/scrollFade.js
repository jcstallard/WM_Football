document.addEventListener('DOMContentLoaded', function () {
    const defensiveSection = document.querySelector('#defense-section');

    const observer = new IntersectionObserver(
        function (entries) {
            entries.forEach(entry => {
                console.log('IntersectionObserver entry:', entry);
                if (entry.isIntersecting) {
                    document.body.classList.add('scrolled');
                } else {
                    document.body.classList.remove('scrolled');
                }
            });
        },
        {
            root: null,
            threshold: 0.2
        }
    );

    if (defensiveSection) {
        observer.observe(defensiveSection);
    } else {
        console.warn('No defensive section found in DOM');
    }
});
