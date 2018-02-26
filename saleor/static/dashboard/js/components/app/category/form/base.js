import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { TextField } from '../../../components/inputs';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import { withStyles } from 'material-ui/styles';
import Button from 'material-ui/Button';

import { CardTitle } from '../../../components/cards';

const styles = {
  cardActions: {
    flexDirection: 'row-reverse'
  },
  textField: {
    marginBottom: '2rem'
  }
};

@withRouter
@withStyles(styles)
class BaseCategoryForm extends Component {
  static propTypes = {
    name: PropTypes.string,
    description: PropTypes.string,
    handleConfirm: PropTypes.func
  };

  constructor(props) {
    super(props);
    this.handleBack = this.handleBack.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.state = {
      formData: {
        name: this.props.name,
        description: this.props.description
      }
    };
  }

  handleBack() {
    this.props.history.goBack();
  }

  handleInputChange(event) {
    const { target } = event;
    this.setState((prevState) => ({
      formData: Object.assign(
        {},
        prevState.formData,
        { [target.name]: target.value }
      )
    }));
  }

  render() {
    const {
      title,
      name,
      description,
      confirmButtonLabel,
      handleConfirm,
      classes
    } = this.props;

    return (
      <Card>
        <CardContent>
          <CardTitle>
            {title}
          </CardTitle>
        </CardContent>
        <CardContent>
          <TextField
            name="name"
            label={pgettext('Category form name field label', 'Name')}
            defaultValue={name}
            className={classes.textField}
            onChange={this.handleInputChange}
          />
          <TextField
            name="description"
            label={`${pgettext('Category form description field label', 'Description')} (${gettext('Optional')})`}
            defaultValue={description}
            multiline={true}
            onChange={this.handleInputChange}
          />
        </CardContent>
        <CardContent>
          <CardActions className={classes.cardActions}>
            <Button
              variant="raised"
              color="secondary"
              onClick={handleConfirm(this.state.formData)}
            >
              {confirmButtonLabel}
            </Button>
            <Button
              color="secondary"
              onClick={this.handleBack}
            >
              {pgettext('Dashboard cancel action', 'Cancel')}
            </Button>
          </CardActions>
        </CardContent>
      </Card>
    );
  };
}

export default BaseCategoryForm;
