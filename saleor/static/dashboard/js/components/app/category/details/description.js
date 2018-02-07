import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import Button from 'material-ui/Button';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';
import { CircularProgress } from 'material-ui/Progress';

import { CardTitle, CardSubtitle } from '../../../components/cards';

const Component = (props) => (
  <div>
    {props.data.loading && (
      <CircularProgress
        size={80}
        thickness={5}
        style={{ margin: 'auto' }}
      />
    )}
    {!props.data.loading && (
      <Card>
        <CardContent>
          <CardTitle>
            {props.data.category.name}
          </CardTitle>
          <CardSubtitle>
          Opis
          </CardSubtitle>
          {props.data.category.description}
          <CardActions>
            <Link to={`/categories/${props.data.category.pk}/edit/`}>
              <Button color={'secondary'}>Edytuj</Button>
            </Link>
            <Link to={`/categories/${props.data.category.parent ? props.data.category.parent.pk : ''}`}>
              <Button color={'secondary'}>Usuń</Button>
            </Link>
          </CardActions>
        </CardContent>
      </Card>
    )}
  </div>
);
const query = gql`
  query CategoryDetails($pk: Int!) {
    category(pk: $pk) {
      pk
      name
      description
      parent {
        pk
      }
    }
  }
`;

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

export default graphql(query, {
  options: (props) => ({
    pk: props.pk
  })
})(Component);
