declare global {
  interface Window {
    gettext(text: string): string;
    pgettext(context: string, text: string): string;
    ngettext(singular: string, plural: string, count: number): string;
    interpolate(text: string, data: Array<any>): string;
  }
}

export const gettext =
  window.gettext instanceof Function ? window.gettext : text => text;

export const pgettext =
  window.pgettext instanceof Function ? window.pgettext : (ctx, text) => text;

export const ngettext =
  window.ngettext instanceof Function
    ? window.ngettext
    : (singular, plural, count) => singular;

export const interpolate =
  window.interpolate instanceof Function
    ? window.interpolate
    : (ctx, text) => text;
