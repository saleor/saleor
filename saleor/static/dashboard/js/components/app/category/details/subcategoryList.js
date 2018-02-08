import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import Table, {
  TableBody,
  TableHead,
  TableRow
} from 'material-ui/Table';
import Card, { CardContent } from 'material-ui/Card';
import Button from 'material-ui/Button';
import gql from 'graphql-tag';
import { graphql } from 'react-apollo';
import { CircularProgress } from 'material-ui/Progress';

import { CardTitle } from '../../../components/cards';
import TableCell from '../../../components/table';

const styleFragments = {
  table: {
    tableLayout: 'auto',
    width: 'calc(100% + 32px)'
  }
};
const styles = {
  cardSubcategories: {
    marginTop: '16px',
    paddingBottom: 0
  },
  table: {
    rootCategory: {
      ...styleFragments.table,
      margin: '-16px'
    },
    childCategory: {
      ...styleFragments.table,
      borderTop: '1px solid rgba(160, 160, 160, 0.2)',
      margin: '0 -16px -26px'
    }
  },
  noSubcategoriesLabel: {
    top: '8px',
    position: 'relative',
    marginLeft: '7px'
  }
};

function handleRowClick(pk, history) {
  history.push(`/categories/${pk}/`);
}

function handleNewCategoryClick(history) {
  return () => history.push('add');
}

const Component = (props) => (
  <Card style={styles.cardSubcategories}>
    {props.data.loading && (
      <CircularProgress
        size={80}
        thickness={5}
        style={{ margin: 'auto' }}
      />
    )}
    {!props.data.loading && (
      <CardContent>
        {props.pk && (
          <div>
            <CardTitle>Subcategories</CardTitle>
            <Button
              color={'secondary'}
              style={{ margin: '2rem 0 1rem' }}
              onClick={handleNewCategoryClick(props.history)}
            >
              Dodaj
            </Button>
          </div>
        )}
        <Table style={props.pk ? styles.table.childCategory : styles.table.rootCategory}>
          <TableHead
            adjustForCheckbox={false}
            displaySelectAll={false}
          >
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell wide>Description</TableCell>
            </TableRow>
          </TableHead>
          <TableBody displayRowCheckbox={false}>
            {props.data.categories.edges.map((edge) => (
              <TableRow
                style={{ cursor: 'pointer' }}
                onClick={() => handleRowClick(edge.node.pk, props.history)}
                key={edge.node.pk}
              >
                <TableCell>{edge.node.name}</TableCell>
                <TableCell wide>{edge.node.description}</TableCell>
              </TableRow>
            ))}
            {!props.data.categories.edges.length && (
              <TableRow style={{ height: '32px' }} />
            )}
          </TableBody>
        </Table>
        {!props.data.categories.edges.length && (
          <div style={styles.noSubcategoriesLabel}>No categories</div>
        )}
      </CardContent>
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
const query = gql`
  query CategoryPage ($pk: Int) {
    categories(parent: $pk) {
      edges {
        node {
          id
          pk
          name
          description
        }
      }
    }
  }
`;

export default withRouter(
  graphql(query, {
    options: (props) => ({
      pk: props.pk
    })
  })(Component)
);
