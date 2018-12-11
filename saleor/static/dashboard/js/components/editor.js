import MediumEditor from 'medium-editor';

import alignCenterIcon from '../../images/editor/align_center.svg';
import alignJustifyIcon from '../../images/editor/align_justify.svg';
import alignLeftIcon from '../../images/editor/align_left.svg';
import alignRightIcon from '../../images/editor/align_right.svg';
import insertLinkIcon from '../../images/editor/insert_link.svg';
import insertPhotoIcon from '../../images/editor/insert_photo.svg';
import quoteIcon from '../../images/editor/quote.svg';
import formatClear from '../../images/editor/format_clear.svg';

import doneIcon from '../../images/done.svg';
import closeIcon from '../../images/close.svg';

// Solve an auto-resize conflict between Materialize and medium-editor.
$('.rich-text-editor').removeClass('materialize-textarea');

// eslint-disable-next-line
const editor = new MediumEditor('.rich-text-editor', {
  paste: {
    forcePlainText: true
  },
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
        aria: pgettext('Rich text editor option', 'Quote'),
        contentDefault: `<img src="${quoteIcon}">`
      },
      {
        name: 'anchor',
        aria: pgettext('Rich text editor option', 'Link'),
        contentDefault: `<img src="${insertLinkIcon}">`,
        formSaveLabel: `<img src="${doneIcon}"`,
        formCloseLabel: `<img src="${closeIcon}">`
      },
      {
        name: 'image',
        aria: pgettext('Rich text editor option', 'Image (converts selected text to an image tag)'),
        contentDefault: `<img src="${insertPhotoIcon}">`
      },
      {
        name: 'justifyLeft',
        aria: pgettext('Rich text editor option', 'Left align'),
        contentDefault: `<img src="${alignLeftIcon}">`
      },
      {
        name: 'justifyCenter',
        aria: pgettext('Rich text editor option', 'Center align'),
        contentDefault: `<img src="${alignCenterIcon}">`
      },
      {
        name: 'justifyRight',
        aria: pgettext('Rich text editor option', 'Right align'),
        contentDefault: `<img src="${alignRightIcon}">`
      },
      {
        name: 'justifyFull',
        aria: pgettext('Rich text editor option', 'Justify'),
        contentDefault: `<img src="${alignJustifyIcon}">`
      },
      {
        name: 'removeFormat',
        aria: pgettext('Rich text editor option', 'Remove formatting'),
        contentDefault: `<img src="${formatClear}">`
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
      }
    ]
  }
});
