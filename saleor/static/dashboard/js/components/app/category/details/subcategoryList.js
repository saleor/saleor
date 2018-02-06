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
    <CardContent>
      {props.category && (
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
      <Table style={props.category ? styles.table.childCategory : styles.table.rootCategory}>
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
          {props.categoryChildren.map((category) => (
            <TableRow style={{ cursor: 'pointer' }}
              onClick={() => handleRowClick(category.pk, props.history)}
              key={category.pk}
            >
              <TableCell>{category.name}</TableCell>
              <TableCell wide>{category.description}</TableCell>
            </TableRow>
          ))}
          {!props.categoryChildren.length && (
            <TableRow style={{ height: '32px' }} />
          )}
        </TableBody>
      </Table>
      {!props.categoryChildren.length && (
        <div style={styles.noSubcategoriesLabel}>No categories</div>
      )}
    </CardContent>
  </Card>
);
Component.propTypes = {
  category: PropTypes.shape({
    pk: PropTypes.number,
    name: PropTypes.string,
    description: PropTypes.string,
    parent: PropTypes.shape({
      pk: PropTypes.number
    })
  }),
  categoryChildren: PropTypes.arrayOf(PropTypes.shape({
    pk: PropTypes.number,
    name: PropTypes.string,
    description: PropTypes.string
  })).isRequired,
  history: PropTypes.object.isRequired
};
export default withRouter(Component);
