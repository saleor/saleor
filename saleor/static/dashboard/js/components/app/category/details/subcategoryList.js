import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import Card, { CardContent } from 'material-ui/Card';
import Button from 'material-ui/Button';
import { graphql } from 'react-apollo';
import { CircularProgress } from 'material-ui/Progress';
import { withStyles } from 'material-ui/styles';

import { CardTitle } from '../../../components/cards';
import Table from '../../../components/table';
import { categoryChildren as query } from '../queries';

const styles = {
  card: {
    paddingBottom: 0
  },
  cardActions: {
    paddingBottom: 0,
  }
};

function handleNewCategoryClick(history) {
  return () => history.push('add');
}

const headers = [
  {
    name: 'name',
    label: 'Name',
    noDataText: 'No name'
  },
  {
    name: 'description',
    label: 'Description',
    wide: true,
    noDataText: 'No description'
  }
];

const Component = (props) => (
  <Card className={props.classes.card}>
    {props.data.loading && (
      <CircularProgress
        size={80}
        thickness={5}
        style={{ margin: 'auto' }}
      />
    )}
    {!props.data.loading && (
      <div>
        {props.pk && (
          <CardContent className={props.classes.cardActions}>
            <CardTitle>Subcategories</CardTitle>
            <Button
              color={'secondary'}
              style={{ margin: '2rem 0 1rem' }}
              onClick={handleNewCategoryClick(props.history)}
            >
              {pgettext('Category list add category', 'Add')}
            </Button>
          </CardContent>
        )}
        <CardContent style={{
          borderTop: props.pk ? '1px solid rgba(160, 160, 160, 0.2)' : 'none',
          padding: 0
        }}>
          <Table
            data={props.data.categories.edges.map((edge) => edge.node)}
            noDataLabel={pgettext('Empty category list message', 'No categories found.')}
            headers={headers}
            href="/categories"
          />
        </CardContent>
      </div>
    )}
  </Card>
);
Component.propTypes = {
  data: PropTypes.shape({
    categories: PropTypes.shape({
      edges: PropTypes.arrayOf(
        PropTypes.shape({
          node: PropTypes.shape({
            pk: PropTypes.number,
            name: PropTypes.string,
            description: PropTypes.string
          })
        })
      )
    }),
    loading: PropTypes.bool
  }),
  pk: PropTypes.number,
  history: PropTypes.object.isRequired
};

export default withStyles(styles)(
  withRouter(
    graphql(query, {
      options: (props) => ({
        pk: props.pk
      })
    })(Component)
  )
);
