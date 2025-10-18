// Apply Dark Mode toggling for PantryCheff
document.addEventListener('DOMContentLoaded', function () {
    const toggleButton = document.getElementById('dark-mode-toggle');
    const html = document.getElementById('html-root');
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');

    // Function to update icons based on current theme
    function updateIcons(isDark) {
        if (isDark) {
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
        } else {
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        }
    }

    // Function to apply theme and update UI
    function applyTheme() {
        const theme = localStorage.getItem('pantrycheff-theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        // Check if theme is explicitly set, otherwise use system preference
        if (theme === 'dark' || (!theme && prefersDark)) {
            html.classList.add('dark');
            updateIcons(true);
            // Update meta theme color for mobile browsers
            updateThemeColor(true);
        } else {
            html.classList.remove('dark');
            updateIcons(false);
            // Update meta theme color for mobile browsers
            updateThemeColor(false);
        }
    }

    // Function to update mobile browser theme color
    function updateThemeColor(isDark) {
        let themeColorMeta = document.querySelector('meta[name="theme-color"]');
        if (!themeColorMeta) {
            themeColorMeta = document.createElement('meta');
            themeColorMeta.name = 'theme-color';
            document.head.appendChild(themeColorMeta);
        }
        themeColorMeta.content = isDark ? '#1f2937' : '#10b981'; // dark: gray-800, light: primary color
    }

    // Function to set theme and save preference
    function setTheme(isDark) {
        if (isDark) {
            html.classList.add('dark');
            localStorage.setItem('pantrycheff-theme', 'dark');
            updateIcons(true);
            updateThemeColor(true);
        } else {
            html.classList.remove('dark');
            localStorage.setItem('pantrycheff-theme', 'light');
            updateIcons(false);
            updateThemeColor(false);
        }
        
        // Dispatch custom event for other components to listen to
        document.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { isDark: isDark } 
        }));
    }

    // Toggle button click handler
    if (toggleButton) {
        toggleButton.addEventListener('click', () => {
            const isDark = html.classList.contains('dark');
            setTheme(!isDark);
        });
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        // Only update if user hasn't set an explicit preference
        if (!localStorage.getItem('pantrycheff-theme')) {
            setTheme(e.matches);
        }
    });

    // Initialize theme on load
    applyTheme();

    // Add smooth transition after initial load to prevent flash
    setTimeout(() => {
        html.classList.add('transition-colors', 'duration-300');
    }, 100);
});

// Optional: Add this to your base template for better transitions
const transitionStyles = `
    .transition-theme * {
        transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
    }
    
    .dark .bg-white {
        background-color: #1f2937;
    }
    
    .dark .bg-gray-50 {
        background-color: #111827;
    }
    
    .dark .border-gray-200 {
        border-color: #374151;
    }
    
    .dark .text-gray-800 {
        color: #f9fafb;
    }
    
    .dark .text-gray-600 {
        color: #d1d5db;
    }
`;

// Inject transition styles
if (!document.querySelector('#theme-transition-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'theme-transition-styles';
    styleSheet.textContent = transitionStyles;
    document.head.appendChild(styleSheet);
}