// match.js — Live search/filter on the dashboard page using jQuery
// Filters skill match cards in real-time as the user types

$(document).ready(function() {
    // Listen for keystrokes in the search box
    $('#matchSearch').on('input', function() {
        var query = $.trim($(this).val()).toLowerCase();

        // Loop through each match card and show/hide based on the query
        $('.match-card').each(function() {
            var name = $(this).data('name') || '';
            var skills = $(this).data('skills') || '';

            if (name.indexOf(query) !== -1 || skills.indexOf(query) !== -1) {
                $(this).fadeIn(200);  // Smooth show with jQuery animation
            } else {
                $(this).fadeOut(200);  // Smooth hide with jQuery animation
            }
        });
    });
});
