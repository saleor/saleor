import React from 'react';
import { action } from '@storybook/addon-actions';
import { storiesOf } from '@storybook/react';

import decorator from '../decorator';
import { ListCard } from '../../saleor/static/dashboard/js/components/app/components/cards';

const headers = [
  {
    name: 'column1',
    label: 'Column 1'
  },
  {
    name: 'column2',
    label: 'Column 2 - wide',
    wide: true
  }
];
const data = [
  { column1: 'Cell 1,1', column2: 'Cell 1,2' },
  { column1: 'Cell 2,1', column2: 'Cell 2,2' },
  { column1: 'Cell 3,1', column2: 'Cell 3,2' }
];

export default storiesOf('ListCard')
  .addDecorator(decorator)
  .add('Default', () => (
    <ListCard
      count={99}
      handleChangePage={action('ChangePageAction')}
      handleChangeRowsPerPage={action('ChangeRowsPerPageAction')}
      handleRowClick={action('RowClickAction')}
      list={[]}
      headers={headers}
      noDataLabel={'No data found'}
      page={0}
      rowsPerPage={10}
    />
  ))
  .add('With label', () => (
    <ListCard
      count={99}
      displayLabel={true}
      handleAddAction={action('AddAction')}
      handleChangePage={action('ChangePageAction')}
      handleChangeRowsPerPage={action('ChangeRowsPerPageAction')}
      handleRowClick={action('RowClickAction')}
      label={'Example card with table'}
      list={[]}
      headers={headers}
      noDataLabel={'No data found'}
      page={0}
      rowsPerPage={10}
    />
  ))
  .add('With data', () => (
    <ListCard
      count={99}
      displayLabel={true}
      handleAddAction={action('AddAction')}
      handleChangePage={action('ChangePageAction')}
      handleChangeRowsPerPage={action('ChangeRowsPerPageAction')}
      handleRowClick={action('RowClickAction')}
      label={'Example card with table'}
      list={data}
      headers={headers}
      noDataLabel={'No data found'}
      page={0}
      rowsPerPage={10}
    />
  ));
