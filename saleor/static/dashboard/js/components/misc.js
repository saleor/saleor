import SVGInjector from 'svg-injector-2';
import MediumEditor from 'medium-editor';

import { initSelects } from './selects';
import { onScroll } from './utils';

const screenSizes = {
  sm: 600,
  md: 992,
  lg: 1200
};

const svgInjector = new SVGInjector();

// -----

// Inject all SVGs
svgInjector.inject(document.querySelectorAll('svg[data-src]'));

// Custom select inputs
initSelects();

// Materialize modals
$('.modal').modal();

// Print button
$('.btn-print').click((e) => {
  window.print();
});

// Clickable rows in dashboard tables
$(document).on('mouseup', 'tr[data-action-go] > td:not(.ignore-link)', (e) => {
  const $target = $(e.currentTarget);
  // Ignore selecting text
  const selectedText = getSelection().toString();
  if (selectedText === '' || selectedText === $target.data('ignore-text')) {
    window.location.href = $target.parent().data('action-go');
  } else {
    $target.data('ignore-text', selectedText);
  }
});

// Publish / unpublish lever in product detail view
$('#product-is-published').on('click', (e) => {
  const form = $(e.currentTarget).closest('#toggle-publish-form');
  const input = form.find('#toggle-publish-switch')[0];
  if (e.target === input) {
    const url = form.attr('action');
    fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
      }
    }).then(() => {
      window.location.reload();
    }).catch(() => {
      window.location.reload();
    });
  }
});

// WYSIWYG editor
new MediumEditor('.rich-text-editor', {
  toolbar: {
    buttons: [
      {
        name: 'bold',
        aria: pgettext('Rich text editor option', 'Bold text')
      },
      {
        name: 'italic',
        aria: pgettext('Rich text editor option', 'Italic text')
      },
      {
        name: 'h2',
        aria: pgettext('Rich text editor option', 'Header'),
        tagNames: ['h2'],
        contentDefault: '<b>T</b>',
        classList: ['custom-class-h1']
      },
      {
        name: 'h3',
        aria: pgettext('Rich text editor option', 'Subheader'),
        tagNames: ['h3'],
        contentDefault: '<b style="font-size: .75rem">T</b>',
        classList: ['custom-class-h2']
      },
      {
        name: 'quote',
        aria: pgettext('Rich text editor option', 'Quote')
      },
      {
        name: 'anchor',
        aria: pgettext('Rich text editor option', 'Link'),
        formSaveLabel: '<img src="/static/dashboard/images/done.svg">',
        formCloseLabel: '<img src="/static/dashboard/images/close.svg">'
      }
    ]
  },
  keyboardCommands: {
    commands: [
      {
        command: 'bold',
        key: 'B',
        meta: true,
        shift: false,
        alt: false
      },
      {
        command: 'italic',
        key: 'I',
        meta: true,
        shift: false,
        alt: false
      },

    ]
  }
});

// Styleguide sticky right menu
onScroll(() => $('.styleguide__menu').toggleClass('fixed', $(window).scrollTop() > 100));

export {
  screenSizes,
  svgInjector
};
