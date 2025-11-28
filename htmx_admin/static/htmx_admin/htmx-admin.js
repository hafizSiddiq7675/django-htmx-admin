/**
 * django-htmx-admin Frontend Controller
 * HTMX-Powered Django Admin Enhancement
 */

(function() {
    'use strict';

    // ========== Toast Notifications ==========

    /**
     * Show a toast notification
     * @param {string} level - Notification level (success, error, warning, info)
     * @param {string} message - Message to display
     * @param {number} duration - Auto-dismiss duration in ms (default: 5000)
     */
    function showToast(level, message, duration) {
        duration = duration || 5000;

        var container = document.getElementById('toast-container');
        var template = document.getElementById('toast-template');

        if (!container || !template) {
            console.warn('Toast container or template not found');
            return;
        }

        var toast = template.content.cloneNode(true).firstElementChild;
        toast.className = 'toast toast-' + level;
        toast.querySelector('.toast-message').textContent = message;

        // Add close button handler
        var closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                dismissToast(toast);
            });
        }

        container.appendChild(toast);

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(function() {
                dismissToast(toast);
            }, duration);
        }
    }

    /**
     * Dismiss a toast with animation
     * @param {HTMLElement} toast - Toast element to dismiss
     */
    function dismissToast(toast) {
        toast.classList.add('toast-fade-out');
        setTimeout(function() {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 300);
    }

    // Listen for showMessage trigger from server
    document.body.addEventListener('showMessage', function(event) {
        var detail = event.detail;
        if (detail && detail.level && detail.message) {
            showToast(detail.level, detail.message);
        }
    });

    // Listen for showMessages trigger (multiple messages)
    document.body.addEventListener('showMessages', function(event) {
        var messages = event.detail;
        if (Array.isArray(messages)) {
            messages.forEach(function(msg) {
                if (msg.level && msg.message) {
                    showToast(msg.level, msg.message);
                }
            });
        }
    });

    // ========== Modal Management ==========

    /**
     * Close and remove the modal
     */
    function closeModal() {
        var modal = document.getElementById('htmx-modal');
        if (modal) {
            modal.classList.add('modal-fade-out');
            setTimeout(function() {
                modal.remove();
            }, 200);
        }
    }

    // Listen for modalClosed trigger from server
    document.body.addEventListener('modalClosed', function() {
        closeModal();
    });

    // Close modal on Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeModal();
        }
    });

    // Close modal on backdrop click
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal-backdrop')) {
            closeModal();
        }
    });

    // ========== Row Deletion Animation ==========

    // Listen for rowDeleted trigger from server
    document.body.addEventListener('rowDeleted', function(event) {
        var detail = event.detail;
        if (detail && detail.id) {
            var row = document.querySelector('[data-row-id="' + detail.id + '"]');
            if (row) {
                row.classList.add('row-fade-out');
                setTimeout(function() {
                    row.remove();
                }, 300);
            }
        }
    });

    // ========== Table Refresh ==========

    // Listen for tableRefresh trigger from server
    document.body.addEventListener('tableRefresh', function() {
        var tableContainer = document.getElementById('result-list-container');
        if (tableContainer) {
            // HTMX will handle the refresh via hx-trigger on the container
            htmx.trigger(tableContainer, 'tableRefresh');
        }
    });

    // ========== Cell Update Feedback ==========

    // Listen for cellUpdated trigger from server
    document.body.addEventListener('cellUpdated', function(event) {
        // Optional: Add visual feedback for successful cell update
        var target = event.target;
        if (target && target.classList) {
            target.classList.add('cell-updated');
            setTimeout(function() {
                target.classList.remove('cell-updated');
            }, 1000);
        }
    });

    // ========== Form Success ==========

    // Listen for formSuccess trigger from server
    document.body.addEventListener('formSuccess', function() {
        // Close any open modals
        closeModal();
    });

    // ========== HTMX Event Handlers ==========

    // Before HTMX sends a request
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        // Add loading class
        var element = event.detail.elt;
        if (element) {
            element.classList.add('htmx-loading');
        }
    });

    // After HTMX request completes
    document.body.addEventListener('htmx:afterRequest', function(event) {
        // Remove loading class
        var element = event.detail.elt;
        if (element) {
            element.classList.remove('htmx-loading');
        }
    });

    // Handle HTMX errors
    document.body.addEventListener('htmx:responseError', function(event) {
        showToast('error', 'An error occurred. Please try again.');
    });

    // Handle HTMX network errors
    document.body.addEventListener('htmx:sendError', function(event) {
        showToast('error', 'Network error. Please check your connection.');
    });

    // ========== CSRF Token Handling ==========

    // Get CSRF token from cookie
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Configure HTMX to include CSRF token
    document.body.addEventListener('htmx:configRequest', function(event) {
        // Add CSRF token to all non-GET requests
        if (event.detail.verb !== 'get') {
            var csrfToken = getCookie('csrftoken');
            if (csrfToken) {
                event.detail.headers['X-CSRFToken'] = csrfToken;
            }
        }
    });

    // ========== Utility Functions ==========

    // Expose utilities globally for custom usage
    window.htmxAdmin = {
        showToast: showToast,
        closeModal: closeModal,
        getCookie: getCookie
    };

    // ========== Initialize ==========

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('django-htmx-admin initialized');
    });

})();
