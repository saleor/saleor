const months = ['January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December'];
const weekdays = ['Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday'];

// -----

$('.datepicker').pickadate({
  // The title label to use for the month nav buttons
  labelMonthNext: pgettext('Datepicker option', 'Next month'),
  labelMonthPrev: pgettext('Datepicker option', 'Previous month'),

  // The title label to use for the dropdown selectors
  labelMonthSelect: pgettext('Datepicker option', 'Select a month'),
  labelYearSelect: pgettext('Datepicker option', 'Select a year'),

  // Months and weekdays
  monthsFull: months.map(month => pgettext('Datepicker month', month)),
  monthsShort: months.map(month => pgettext('Datepicker month shortcut', month.slice(0, 3))),
  weekdaysFull: weekdays.map(day => pgettext('Datepicker weekday', day)),
  weekdaysShort: weekdays.map(day => pgettext('Datepicker weekday shortcut', day.slice(0, 3))),

  // Materialize modified
  weekdaysLetter: weekdays.map(day => pgettext(`${day} shortcut`, day[0])),
  today: pgettext('Datepicker option', 'Today'),
  clear: pgettext('Datepicker option', 'Clear'),
  close: pgettext('Datepicker option', 'Close'),

  format: 'd mmmm yyyy',
  formatSubmit: 'yyyy-mm-dd',
  selectMonths: true,
  hiddenName: true,
  onClose: () => $(document.activeElement).blur()
});
