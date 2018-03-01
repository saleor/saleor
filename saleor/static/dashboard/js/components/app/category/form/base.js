import React, { Component } from 'react';
import Button from 'material-ui/Button';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import PropTypes from 'prop-types';
import Typography from 'material-ui/Typography';
import { withRouter } from 'react-router-dom';
import { withStyles } from 'material-ui/styles';

import { TextField } from '../../components/inputs';

const styles = {
  cardActions: {
    flexDirection: 'row-reverse',
  },
  textField: {
    marginBottom: '2rem',
  },
};

@withRouter
@withStyles(styles)
class BaseCategoryForm extends Component {
  static propTypes = {
    classes: PropTypes.object,
    confirmButtonLabel: PropTypes.string,
    description: PropTypes.string,
    handleConfirm: PropTypes.func,
    history: PropTypes.object,
    name: PropTypes.string,
    title: PropTypes.string,
  };

  constructor(props) {
    super(props);
    this.handleBack = this.handleBack.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.state = {
      formData: {
        description: this.props.description,
        name: this.props.name,
      },
    };
  }

  handleBack() {
    this.props.history.goBack();
  }

  handleInputChange(event) {
    const { target } = event;
    this.setState(prevState => ({
      formData: Object.assign(
        {},
        prevState.formData,
        { [target.name]: target.value },
      ),
    }));
  }

  render() {
    const {
      classes,
      confirmButtonLabel,
      description,
      handleConfirm,
      name,
      title,
    } = this.props;

    return (
      <Card>
        <CardContent>
          <Typography variant="display1">
            {title}
          </Typography>
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
            multiline
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
  }
}

export default BaseCategoryForm;
