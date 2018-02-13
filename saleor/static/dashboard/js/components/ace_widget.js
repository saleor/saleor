import $ from 'jquery';
import ace from 'brace';

require('brace/mode/javascript');
require('brace/mode/html');
require('brace/theme/monokai');

function setEditor(editor, langMode) {
  editor.setTheme('ace/theme/monokai');
  editor.session.setUseWrapMode(true);
  editor.session.setMode(`ace/mode/${langMode}`);
  editor.setShowPrintMargin(false);
  editor.setHighlightActiveLine(true);
}

function setAceWidget(name) {
  const $textarea = $(`textarea[name='${name}']`);
  const aceEditor = ace.edit(name);
  const $editor = $(`#${name}`);
  const langMode = $editor.data('mode');
  aceEditor.$blockScrolling = Infinity;
  setEditor(aceEditor, langMode);
  aceEditor.session.setValue($textarea.val());
  aceEditor.session.on('change', () => {
    $textarea.text(aceEditor.getSession().getValue());
  });
}

$(document).ready(() => {
  const aceWidgets = $('.ace-editor');
  aceWidgets.each((index, element) => {
    setAceWidget(element.id);
  });
});
