import React from 'react';
import { TableCell as MuiTableCell } from 'material-ui/Table';
import { withStyles } from 'material-ui/styles';


const styleFragments = {
  tableCell: {
    fontSize: '12px',
  },
};
const styles = {
  tableCell: {
    root: {
      ...styleFragments.tableCell,
    },
  },
  wideTableCell: {
    root: {
      ...styleFragments.tableCell,
      width: '99%',
    },
  },
};
const TableCell = withStyles(styles.tableCell)((props) => {
  return <MuiTableCell {...props}/>
});
const WideTableCell = withStyles(styles.wideTableCell)((props) => {
  return <MuiTableCell {...props}/>
});

export {
  TableCell,
  WideTableCell,
};
