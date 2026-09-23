// Browser storage and file picking, adapted from Ghostship's src/port/web (MIT).
#ifdef __EMSCRIPTEN__
#include "WebUtils.h"

#include <emscripten.h>
#include <SDL2/SDL_timer.h>
#include <ship/Context.h>

// clang-format off
EM_JS(void, js_idbfs_mount, (const char* cpath), {
    var path = UTF8ToString(cpath);
    try {
        FS.mkdir(path);
    } catch (e) {}
    FS.mount(IDBFS, {}, path);
});

EM_ASYNC_JS(void, js_idbfs_sync, (int populate), {
    await new Promise(function(resolve) {
        FS.syncfs(!!populate, function(err) {
            if (err) {
                console.error('[WebStorage] sync failed:', err);
            }
            resolve();
        });
    });
});

EM_JS(void, js_idbfs_sync_nowait, (), {
    FS.syncfs(false, function(err) {
        if (err) {
            console.error('[WebStorage] sync failed:', err);
        }
    });
});

// Safari only opens a file dialog from inside a user gesture, and the game loop is not one,
// so this shows an in-page prompt and opens the dialog from its button's click handler.
EM_ASYNC_JS(int, js_pick_into, (const char* ctitle, const char* caccept, const char* cdest), {
    var title = UTF8ToString(ctitle);
    var accept = UTF8ToString(caccept);
    var dest = UTF8ToString(cdest);
    return await new Promise(function(resolve) {
        var overlay = document.createElement('div');
        overlay.className = 'soh-prompt';
        var panel = document.createElement('div');
        panel.className = 'soh-prompt-panel';
        var label = document.createElement('p');
        label.textContent = title;
        var input = document.createElement('input');
        input.type = 'file';
        input.accept = accept;
        input.style.display = 'none';
        var choose = document.createElement('button');
        choose.textContent = 'Choose file';
        var cancel = document.createElement('button');
        cancel.textContent = 'Cancel';
        var settled = false;
        function finish(result) {
            if (settled) return;
            settled = true;
            if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
            resolve(result);
        }
        input.addEventListener('change', function(evt) {
            var file = evt.target.files[0];
            if (!file) { finish(0); return; }
            label.textContent = 'Reading ' + file.name + '...';
            file.arrayBuffer().then(function(buf) {
                try {
                    FS.writeFile(dest, new Uint8Array(buf));
                    finish(1);
                } catch (e) {
                    console.error('[WebFilePicker] write failed:', e);
                    finish(0);
                }
            }, function() { finish(0); });
        });
        choose.addEventListener('click', function() { input.click(); });
        cancel.addEventListener('click', function() { finish(0); });
        panel.appendChild(label);
        panel.appendChild(input);
        panel.appendChild(choose);
        panel.appendChild(cancel);
        overlay.appendChild(panel);
        document.body.appendChild(overlay);
    });
});
// clang-format on

extern "C" void WebStorage_Mount(void) {
    static bool sMounted = false;
    if (sMounted) {
        return;
    }
    sMounted = true;
    js_idbfs_mount(Ship::Context::GetAppDirectoryPath().c_str());
    js_idbfs_sync(1);
}

extern "C" void WebStorage_Sync(void) {
    js_idbfs_sync(0);
}

extern "C" void WebStorage_SyncNoWait(void) {
    js_idbfs_sync_nowait();
}

extern "C" void WebStorage_PeriodicSync(void) {
    static uint32_t sLastSync = 0;
    const uint32_t now = SDL_GetTicks();
    if (now - sLastSync > 5000) {
        sLastSync = now;
        WebStorage_Sync();
    }
}

extern "C" int WebFilePicker_PickInto(const char* title, const char* accept, const char* destPath) {
    return js_pick_into(title, accept, destPath);
}

#endif // __EMSCRIPTEN__
