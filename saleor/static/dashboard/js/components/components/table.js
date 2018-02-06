import React from 'react';
import { TableCell } from 'material-ui/Table';
import { withStyles } from 'material-ui/styles';

const styles = {
  wideTableCell: {
    width: '99%'
  }
};

export default withStyles(styles)(
  (props) => {
    let wideComponent = false;
    if (props.wide) {
      wideComponent = true;
      delete props.wide;
    }
    const {classes, ...componentProps} = props;
    return (
      <TableCell
        classes={wideComponent ? {root: classes.wideTableCell} : {}}
        {...componentProps}
      />
    );
  }
);
