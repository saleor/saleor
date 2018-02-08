import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withStyles } from 'material-ui/styles';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import Button from 'material-ui/Button';
import { CircularProgress } from 'material-ui/Progress';

import { TextField } from '../../components/inputs';
import SubmitButton from './submitButton';

const styles = theme => ({
  cardActions: {
    marginLeft: 0,
    marginRight: 0,
    justifyContent: 'flex-end'
  },
  inputContainer: {
    marginBottom: theme.spacing.unit * 2
  },
  largeTextInput: {
    '& input': {
      fontSize: '2.2rem'
    }
  }
});

class CategoryEdit extends Component {
  static propTypes = {
    pk: PropTypes.number.isRequired,
    data: PropTypes.shape({
      category: PropTypes.shape({
        pk: PropTypes.number,
        name: PropTypes.string,
        description: PropTypes.string,
        parent: PropTypes.shape({
          pk: PropTypes.number
        })
      }),
      loading: PropTypes.bool
    })
  };

  constructor(props) {
    super(props);
    this.handleBack = this.handleBack.bind(this);
    this.handleFieldChange = this.handleFieldChange.bind(this);
    this.state = {
      name: '',
      description: '',
    };
  }

  handleBack() {
    this.props.history.push(`/categories/${this.props.pk}`);
  }

  handleFieldChange(event) {
    this.setState({
      [event.target.name]: event.target.value
    });
  }

  componentWillReceiveProps(props) {
    this.setState({
      name: props.data.category.name,
      description: props.data.category.description,
    });
  }

  render() {
    return (
      <div>
        {this.props.data.loading && (
          <CircularProgress
            size={80}
            thickness={5}
            style={{ margin: 'auto' }}
          />
        )}
        {!this.props.data.loading && (
          <Card>
            <CardContent>
              <div className={this.props.classes.inputContainer}>
                <TextField
                  name={'name'}
                  label={'Name'}
                  defaultValue={this.props.data.category.name}
                  className={this.props.classes.largeTextInput}
                  onChange={this.handleFieldChange}
                  required
                />
              </div>
              <div className={this.props.classes.inputContainer}>
                <TextField
                  name={'description'}
                  label={'Description (optional)'}
                  defaultValue={this.props.data.category.description}
                  onChange={this.handleFieldChange}
                  multiline
                />
              </div>
            </CardContent>
            <CardActions classes={{ root: this.props.classes.cardActions }}>
              <Button
                color="secondary"
                onClick={this.handleBack}
              >
                Anuluj
              </Button>
              <SubmitButton
                action={this.props.action}
                name={this.state.name}
                description={this.state.description}
                parent={this.props.data.category.pk}
              >
                {this.props.action === 'ADD' ? 'Utwórz' : 'Aktualizuj'}
              </SubmitButton>
            </CardActions>
          </Card>
        )}
      </div>
    );
  }
}

export default withStyles(styles)(withRouter(CategoryEdit));
