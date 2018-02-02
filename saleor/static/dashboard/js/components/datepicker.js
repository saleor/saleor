// -----

$('.datepicker').pickadate({
  labelMonthNext: pgettext('Datepicker option', 'Next month'),
  labelMonthPrev: pgettext('Datepicker option', 'Previous month'),

  // The title label to use for the dropdown selectors
  labelMonthSelect: pgettext('Datepicker option', 'Select a month'),
  labelYearSelect: pgettext('Datepicker option', 'Select a year'),

  // Months and weekdays
  monthsFull: [
    pgettext('Datepicker month', 'January'),
    pgettext('Datepicker month', 'February'),
    pgettext('Datepicker month', 'March'),
    pgettext('Datepicker month', 'April'),
    pgettext('Datepicker month', 'May'),
    pgettext('Datepicker month', 'June'),
    pgettext('Datepicker month', 'July'),
    pgettext('Datepicker month', 'August'),
    pgettext('Datepicker month', 'September'),
    pgettext('Datepicker month', 'October'),
    pgettext('Datepicker month', 'November'),
    pgettext('Datepicker month', 'December')],
  monthsShort: [
    pgettext('Datepicker month shortcut', 'Jan'),
    pgettext('Datepicker month shortcut', 'Feb'),
    pgettext('Datepicker month shortcut', 'Mar'),
    pgettext('Datepicker month shortcut', 'Apr'),
    pgettext('Datepicker month shortcut', 'May'),
    pgettext('Datepicker month shortcut', 'Jun'),
    pgettext('Datepicker month shortcut', 'Jul'),
    pgettext('Datepicker month shortcut', 'Aug'),
    pgettext('Datepicker month shortcut', 'Sep'),
    pgettext('Datepicker month shortcut', 'Oct'),
    pgettext('Datepicker month shortcut', 'Nov'),
    pgettext('Datepicker month shortcut', 'Dec')],
  weekdaysFull: [
    pgettext('Datepicker weekday', 'Sunday'),
    pgettext('Datepicker weekday', 'Monday'),
    pgettext('Datepicker weekday', 'Tuesday'),
    pgettext('Datepicker weekday', 'Wednesday'),
    pgettext('Datepicker weekday', 'Thursday'),
    pgettext('Datepicker weekday', 'Friday'),
    pgettext('Datepicker weekday', 'Saturday')],
  weekdaysShort: [
    pgettext('Datepicker weekday shortcut', 'Sun'),
    pgettext('Datepicker weekday shortcut', 'Mon'),
    pgettext('Datepicker weekday shortcut', 'Tue'),
    pgettext('Datepicker weekday shortcut', 'Wed'),
    pgettext('Datepicker weekday shortcut', 'Thu'),
    pgettext('Datepicker weekday shortcut', 'Fri'),
    pgettext('Datepicker weekday shortcut', 'Sat')],

  // Materialize modified
  weekdaysLetter: [
    pgettext('Sunday shortcut', 'S'),
    pgettext('Monday shortcut', 'M'),
    pgettext('Tuesday shortcut', 'T'),
    pgettext('Wednesday shortcut', 'W'),
    pgettext('Thursday shortcut', 'T'),
    pgettext('Friday shortcut', 'F'),
    pgettext('Saturday shortcut', 'S')],
  today: pgettext('Datepicker option', 'Today'),
  clear: pgettext('Datepicker option', 'Clear'),
  close: pgettext('Datepicker option', 'Close'),

  format: 'd mmmm yyyy',
  formatSubmit: 'yyyy-mm-dd',
  selectMonths: true,
  hiddenName: true,
  onClose: () => $(document.activeElement).blur()
});
