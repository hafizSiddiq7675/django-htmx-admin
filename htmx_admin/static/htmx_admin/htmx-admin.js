/**
 * django-htmx-admin Frontend Controller
 * HTMX-Powered Django Admin Enhancement
 */

(function() {
    'use strict';

    // Prevent multiple initializations
    if (window.htmxAdminInitialized) {
        return;
    }
    window.htmxAdminInitialized = true;

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
            // Fallback: create a simple alert if containers not found
            console.log('[' + level + '] ' + message);
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

    // ========== CSRF Token Handling ==========

    /**
     * Get CSRF token from cookie
     * @param {string} name - Cookie name
     * @returns {string|null} - Cookie value
     */
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

    // ========== Pagination Count Updates ==========

    /**
     * Update pagination counts after table refresh
     * Counts the rows in the table and updates all pagination elements
     */
    function updatePaginationCounts() {
        // Count rows in the table
        var table = document.getElementById('result_list');
        if (!table) return;

        var rows = table.querySelectorAll('tbody tr[data-row-id]');
        var count = rows.length;

        // Update Grappelli pagination (li.grp-results)
        var grpResults = document.querySelectorAll('li.grp-results');
        grpResults.forEach(function(el) {
            el.innerHTML = '<span>' + count + ' total</span>';
        });

        // Update default Django admin pagination (.paginator)
        var paginators = document.querySelectorAll('.paginator:not(.grp-pagination)');
        paginators.forEach(function(el) {
            // Check if it's a count display (not the page navigation)
            if (el.textContent.match(/\d+\s*(total|results?)/i)) {
                el.innerHTML = count + ' total';
            }
        });
    }

    // ========== Expose utilities globally ==========
    window.htmxAdmin = {
        showToast: showToast,
        closeModal: closeModal,
        getCookie: getCookie,
        updatePaginationCounts: updatePaginationCounts
    };

    // ========== Initialize Event Listeners ==========

    function initEventListeners() {
        // Ensure body exists
        if (!document.body) {
            console.warn('htmx-admin: document.body not available');
            return;
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

        // Listen for modalClosed trigger from server
        document.body.addEventListener('modalClosed', function() {
            closeModal();
        });

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

        // Note: Table refresh is handled by HTMX via hx-trigger="refreshTable from:body"
        // The backend sends HX-Trigger: refreshTable header which HTMX catches automatically

        // Update pagination counts after table refresh
        document.body.addEventListener('htmx:afterSwap', function(event) {
            var target = event.detail.target;
            if (target && target.id === 'result-list-container') {
                updatePaginationCounts();
            }
        });

        // Listen for cellUpdated trigger from server
        document.body.addEventListener('cellUpdated', function(event) {
            var target = event.target;
            if (target && target.classList) {
                target.classList.add('cell-updated');
                setTimeout(function() {
                    target.classList.remove('cell-updated');
                }, 1000);
            }
        });

        // Listen for formSuccess trigger from server
        document.body.addEventListener('formSuccess', function() {
            closeModal();
        });

        // ========== HTMX Event Handlers ==========

        // Before HTMX sends a request
        document.body.addEventListener('htmx:beforeRequest', function(event) {
            var element = event.detail.elt;
            if (element) {
                element.classList.add('htmx-loading');
            }
        });

        // After HTMX request completes
        document.body.addEventListener('htmx:afterRequest', function(event) {
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

        // Configure HTMX to include CSRF token
        document.body.addEventListener('htmx:configRequest', function(event) {
            if (event.detail.verb !== 'get') {
                var csrfToken = getCookie('csrftoken');
                if (csrfToken) {
                    event.detail.headers['X-CSRFToken'] = csrfToken;
                }
            }
        });

        // ========== Document Event Handlers ==========

        // Close modal on Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeModal();
            }
        });

        // Close modal on backdrop click
        document.addEventListener('click', function(event) {
            if (event.target.classList && event.target.classList.contains('modal-backdrop')) {
                closeModal();
            }
        });

        console.log('django-htmx-admin initialized');
    }

    // ========== Initialize on DOM Ready ==========

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEventListeners);
    } else {
        // DOM already loaded
        initEventListeners();
    }

})();
