import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Link, withRouter } from 'react-router-dom';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import Button from 'material-ui/Button';
import { graphql, compose } from 'react-apollo';
import { CircularProgress } from 'material-ui/Progress';

import { CardTitle, CardSubtitle } from '../../../components/cards';
import { ConfirmRemoval } from '../../../components/modals';
import { CategoryDetails as query } from '../queries';
import { deleteCategory as mutation } from '../mutations';

class CategoryDescription extends Component {
  constructor(props) {
    super(props);
    this.state = { opened: false };
    this.handleModalOpen = this.handleModalOpen.bind(this);
    this.handleModalClose = this.handleModalClose.bind(this);
    this.handleRemoval = this.handleRemoval.bind(this);
  }

  handleModalOpen() {
    this.setState({ opened: true });
  }

  handleModalClose() {
    this.setState({ opened: false });
  }

  handleRemoval() {
    const parentPk = this.props.data.category.parent.pk;
    this.props.mutate({
      pk: this.props.data.category.pk
    }).then(this.handleModalClose)
      .then(() => this.props.history.push(`/categories/${parentPk}/`))
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
          <div>
            <Card>
              <CardContent>
                <CardTitle>
                  {this.props.data.category.name}
                </CardTitle>
                <CardSubtitle>
                  Opis
                </CardSubtitle>
                {this.props.data.category.description}
                <CardActions>
                  <Link to={`/categories/${this.props.data.category.pk}/edit/`}>
                    <Button color={'secondary'}>Edytuj</Button>
                  </Link>
                  {/*<Link to={`/categories/${props.data.category.parent ? props.data.category.parent.pk : ''}`}>*/}
                  {/*<Button color={'secondary'}>Usuń</Button>*/}
                  {/*</Link>*/}
                  <Button
                    color={'secondary'}
                    onClick={this.handleModalOpen}
                  >
                    Usuń
                  </Button>
                </CardActions>
              </CardContent>
            </Card>
            <ConfirmRemoval
              open={this.state.opened}
              onClose={this.handleModalClose}
              onConfirm={this.handleRemoval}
              content={`Are you sure you want to delete category ${this.props.data.category.name}?`}
            />
          </div>
        )}
      </div>
    );
  }
}

Component.propTypes = {
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

export default compose(
  withRouter,
  graphql(query, {
    options: (props) => ({
      pk: props.pk
    })
  }),
  graphql(mutation, {
    options: {
      refetchQueries: [
        'CategoryPage',
        'CategoryDetails',
      ]
    }
  })
)(CategoryDescription);
