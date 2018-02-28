export let gettext = window.gettext instanceof Function ? window.gettext : (text) => text;
export let pgettext = window.pgettext instanceof Function ? window.pgettext : (ctx, text) => text;
export let ngettext = window.ngettext instanceof Function ? window.ngettext : (ctx, text) => text;
export let interpolate = window.interpolate instanceof Function ? window.interpolate : (ctx, text) => text;
