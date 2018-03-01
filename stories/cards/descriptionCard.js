import React from 'react';
import { action } from '@storybook/addon-actions';
import { storiesOf } from '@storybook/react';

import decorator from '../decorator';
import { DescriptionCard } from '../../saleor/static/dashboard/js/components/app/components/cards';

export default storiesOf('DescriptionCard')
  .addDecorator(decorator)
  .add('Default', () => (
    <DescriptionCard
      description={'This is example card description. This text should not be too long - long enough to make reading person to interest, but short enough not to overwhelm user with massive wall of text.'}
      descriptionTextLabel={'Description'}
      editButtonLabel={'Edit'}
      handleEditButtonClick={action('EditAction')}
      handleRemoveButtonClick={action('RemoveAction')}
      removeButtonLabel={'Remove'}
      title={'Example description card'}
    />
  ));
