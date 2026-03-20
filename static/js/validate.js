// validate.js — Client-side form validation using jQuery
// Validates registration and login forms before submission

$(document).ready(function() {

    // ─── Registration Form Validation ────────────────────
    $('#registerForm').on('submit', function(e) {
        var valid = true;
        var $name = $('#name');
        var $email = $('#email');
        var $password = $('#password');

        // Reset previous error styles
        clearErrors([$name, $email, $password]);

        // Validate Name: must be at least 2 characters
        if ($.trim($name.val()).length < 2) {
            showError($name, '#nameError', 'Name must be at least 2 characters.');
            valid = false;
        }

        // Validate Email: must contain @ and a dot
        var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test($.trim($email.val()))) {
            showError($email, '#emailError', 'Please enter a valid email address.');
            valid = false;
        }

        // Validate Password: must be at least 6 characters
        if ($password.val().length < 6) {
            showError($password, '#passwordError', 'Password must be at least 6 characters.');
            valid = false;
        }

        // If any field is invalid, prevent form submission
        if (!valid) {
            e.preventDefault();
        }
    });

    // ─── Login Form Validation ───────────────────────────
    $('#loginForm').on('submit', function(e) {
        var valid = true;
        var $email = $('#email');
        var $password = $('#password');

        clearErrors([$email, $password]);

        if ($.trim($email.val()) === '') {
            $email.addClass('is-invalid');
            valid = false;
        }

        if ($.trim($password.val()) === '') {
            $password.addClass('is-invalid');
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
        }
    });

    // ─── Real-time password strength indicator ───────────
    $('#password').on('input', function() {
        var len = $(this).val().length;
        var $hint = $('#passwordHint');

        if ($hint.length === 0) {
            $(this).after('<small id="passwordHint" class="form-text"></small>');
            $hint = $('#passwordHint');
        }

        if (len === 0) {
            $hint.text('').hide();
        } else if (len < 6) {
            $hint.text('Weak password').css('color', '#dc3545').show();
        } else if (len < 10) {
            $hint.text('Moderate password').css('color', '#ffc107').show();
        } else {
            $hint.text('Strong password').css('color', '#198754').show();
        }
    });

    // ─── Helper Functions ────────────────────────────────

    /**
     * showError — Marks an input as invalid and shows an error message.
     * Uses jQuery to add Bootstrap's is-invalid class and set error text.
     */
    function showError($input, errorSelector, message) {
        $input.addClass('is-invalid');
        $(errorSelector).text(message);
    }

    /**
     * clearErrors — Removes invalid styling from a list of jQuery elements.
     */
    function clearErrors(inputs) {
        $.each(inputs, function(i, $input) {
            $input.removeClass('is-invalid');
        });
    }
});
