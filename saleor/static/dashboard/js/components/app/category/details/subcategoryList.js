import React from 'react';
import { withRouter } from 'react-router-dom';
import Table, {
  TableBody,
  TableHead,
  TableRow
} from 'material-ui/Table';
import Card, { CardContent } from 'material-ui/Card';

import { FlatButton } from '../../../components/buttons';
import { CardTitle } from '../../../components/cards';
import { TableCell, WideTableCell } from '../../../components/table';


const styleFragments = {
  table: {
    tableLayout: 'auto',
    width: 'calc(100% + 32px)'
  },
};
const styles = {
  cardSubcategories: {
    marginTop: '16px',
    paddingBottom: 0,
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
const handleRowClick = (pk, history) => {
  history.push(pk);
};
export default withRouter((props) => (
  <Card style={styles.cardSubcategories}>
    <CardContent>
      {props.category && (
        <div>
          <CardTitle>Subcategories</CardTitle>
          <FlatButton color={'secondary'} style={{ margin: '2rem 0 1rem' }}>Dodaj</FlatButton>
        </div>
      )}
      <Table style={props.category ? styles.table.childCategory : styles.table.rootCategory}>
        <TableHead adjustForCheckbox={false}
                   displaySelectAll={false}>
          <TableRow>
            <TableCell>Name</TableCell>
            <WideTableCell wide>Description</WideTableCell>
          </TableRow>
        </TableHead>
        <TableBody displayRowCheckbox={false}>
          {props.children.map((category) => (
            <TableRow style={{ cursor: 'pointer' }}
                      onClick={() => handleRowClick(category.pk, props.history)}
                      key={category.pk}>
              <TableCell>{category.name}</TableCell>
              <WideTableCell>{category.description}</WideTableCell>
            </TableRow>
          ))}
          {!props.children.length && (
            <TableRow style={{ height: '32px' }} />
          )}
        </TableBody>
      </Table>
      {!props.children.length && (
        <div style={styles.noSubcategoriesLabel}>No categories</div>
      )}
    </CardContent>
  </Card>
));
