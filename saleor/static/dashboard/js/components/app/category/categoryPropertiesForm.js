import React, { Component } from 'react';
import { compose, graphql } from 'react-apollo';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withStyles } from 'material-ui/styles';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import Button from 'material-ui/Button';
import { CircularProgress } from 'material-ui/Progress';

import { TextField } from '../../components/inputs';
import { categoryCreate, categoryUpdate } from './mutations';
import { categoryChildren, categoryDetails } from './queries';

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
      fontSize: theme.typography.display1.fontSize
    }
  }
});
const createMutation = graphql(categoryCreate, {
  options: (props) => ({
    refetchQueries: [
      {
        query: categoryChildren,
        variables: { pk: props.data.category.parent ? props.data.category.parent.pk : '' }
      }
    ]
  }),
  name: 'categoryCreate'
});
const updateMutation = graphql(categoryUpdate, {
  options: (props) => ({
    refetchQueries: [
      {
        query: categoryChildren,
        variables: { pk: props.pk }
      },
      {
        query: categoryDetails,
        variables: { pk: props.pk }
      }
    ]
  }),
  name: 'categoryUpdate'
});

@withStyles(styles)
@withRouter
@compose(createMutation, updateMutation)
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
    }),
    classes: PropTypes.object,
    action: PropTypes.string,
    history: PropTypes.object
  };

  constructor(props) {
    super(props);
    this.handleBack = this.handleBack.bind(this);
    this.handleFieldChange = this.handleFieldChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.state = {
      name: '',
      description: ''
    };
  }

  handleBack() {
    this.props.history.goBack();
  }

  handleFieldChange(event) {
    this.setState({
      [event.target.name]: event.target.value
    });
  }

  handleSubmit() {
    let mutation;
    switch (this.props.action) {
      case 'CREATE':
        mutation = 'categoryCreate';
        break;
      case 'UPDATE':
        mutation = 'categoryUpdate';
        break;
    }
    if (mutation) {
      this.props[mutation]({
        variables: {
          name: this.state.name,
          description: this.state.description,
          parent: this.props.data.category.parent.pk,
          pk: this.props.pk
        }
      })
        .then(({ data }) => {
          this.props.history.push(`/categories/${data[mutation].category.pk}/`);
        });
    }
  }

  componentWillReceiveProps(props) {
    this.setState({
      name: props.data.category.name,
      description: props.data.category.description
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
              <Button
                onClick={this.handleSubmit}
                color="secondary"
                variant="raised"
              >
                {this.props.action === 'ADD' ? 'Utwórz' : 'Aktualizuj'}
              </Button>
            </CardActions>
          </Card>
        )}
      </div>
    );
  }
}

export default CategoryEdit;
