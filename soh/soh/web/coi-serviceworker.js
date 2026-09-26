/* coi-serviceworker makes SharedArrayBuffer available on any host by
 * injecting Cross-Origin-Opener-Policy / Cross-Origin-Embedder-Policy headers
 * via a service worker fetch handler.
 *
 * When loaded inside a page context (window defined) it registers itself as a
 * service worker and reloads once the controller is active. It reloads at most
 * once per attempt, so a host that blocks isolation (for example through
 * Permissions-Policy) gets an error instead of a reload loop.
 * When running AS the service worker (window undefined) it intercepts fetches
 * and adds the required headers to every response.
 *
 * Based on https://github.com/gzuidhof/coi-serviceworker (MIT license).
 */
if (typeof window === 'undefined') {
    // == Service worker context ==============================================
    self.addEventListener('install', () => self.skipWaiting());
    self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

    self.addEventListener('fetch', function (event) {
        // Skip opaque (cache-only) cross-origin requests to avoid breaking them.
        if (event.request.cache === 'only-if-cached' &&
            event.request.mode !== 'same-origin') {
            return;
        }

        event.respondWith(
            fetch(event.request)
                .then(function (response) {
                    if (response.status === 0) return response;

                    const headers = new Headers(response.headers);
                    headers.set('Cross-Origin-Opener-Policy',   'same-origin');
                    headers.set('Cross-Origin-Embedder-Policy', 'require-corp');

                    return new Response(response.body, {
                        status:     response.status,
                        statusText: response.statusText,
                        headers:    headers,
                    });
                })
                .catch((e) => console.error('[coi-sw] fetch error:', e))
        );
    });

} else {
    // == Page context: register the service worker ===========================
    const reloadedKey = 'coiReloaded';
    if (self.crossOriginIsolated) {
        sessionStorage.removeItem(reloadedKey);
    } else if (sessionStorage.getItem(reloadedKey)) {
        sessionStorage.removeItem(reloadedKey);
        console.error('[coi-sw] Still not cross-origin isolated after reloading; the host may block it.');
    } else {
        const swSrc = document.currentScript
            ? document.currentScript.src
            : 'coi-serviceworker.js';
        const reload = () => {
            sessionStorage.setItem(reloadedKey, '1');
            location.reload();
        };

        navigator.serviceWorker.register(swSrc)
            .then(() => {
                // If we already have a controller the SW can serve us immediately.
                if (navigator.serviceWorker.controller) {
                    reload();
                } else {
                    // Wait for the SW to take control, then reload so the new
                    // headers are applied from the start.
                    navigator.serviceWorker.addEventListener('controllerchange', reload);
                }
            })
            .catch((err) => {
                console.error('[coi-sw] Registration failed:', err);
            });
    }
}
