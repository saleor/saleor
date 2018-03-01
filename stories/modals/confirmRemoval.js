import React, { Component, Fragment } from 'react';
import Button from 'material-ui/Button';
import Typography from 'material-ui/Typography';
import { action } from '@storybook/addon-actions';
import { storiesOf } from '@storybook/react';

import decorator from '../decorator';
import { ConfirmRemoval } from '../../saleor/static/dashboard/js/components/app/components/modals';

class ModalContainer extends Component {
  constructor(props) {
    super(props);
    this.state = { opened: false };
  }

  handleModalToggle = () => {
    this.setState((prevState) => ({ opened: !prevState.opened }));
  };

  render () {
    return (
      <Fragment>
        <Button
          color={"secondary"}
          onClick={this.handleModalToggle}
          variant={"raised"}
        >
          Open modal
        </Button>
        <ConfirmRemoval
          title={"Confirm removal"}
          opened={this.state.opened}
          onConfirm={action('ConfirmAction')}
          onClose={this.handleModalToggle}
        >
          <Typography>
            Are you sure?
          </Typography>
        </ConfirmRemoval>
      </Fragment>
    )
  }
}

export default storiesOf('ConfirmRemovalModal')
  .addDecorator(decorator)
  .add('Default', () => (
    <ModalContainer/>
  ));
