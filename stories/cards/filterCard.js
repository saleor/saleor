import React from 'react';
import { action } from '@storybook/addon-actions';
import { storiesOf } from '@storybook/react';

import decorator from '../decorator';
import { FilterCard } from '../../saleor/static/dashboard/js/components/app/components/cards';
import { TextField } from '../../saleor/static/dashboard/js/components/app/components/inputs';

export default storiesOf('FilterCard')
  .addDecorator(decorator)
  .add('Default', () => (
    <FilterCard
      handleClear={action('ClearAction')}
      handleSubmit={action('SubmitAction')}
    />
  ))
  .add('With text input', () => (
    <FilterCard
      handleClear={action('ClearAction')}
      handleSubmit={action('SubmitAction')}
    >
      <TextField
        label={'Example input'}
      />
    </FilterCard>
  ));
