import MediumEditor from 'medium-editor';

// eslint-disable
const editor = new MediumEditor('.rich-text-editor', {
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
      }
    ]
  }
});
