import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import MuiTable, {
  TableHead,
  TableBody,
  TableRow,
  TableCell as MuiTableCell
} from 'material-ui/Table';
import { withStyles } from 'material-ui/styles';

const styles = {
  wideTableCell: {
    width: '99%'
  },
  childCategory: {
    tableLayout: 'auto'
  },
  noDataText: {
    marginTop: -8,
    top: 8,
    position: 'relative',
    borderTop: '1px solid rgba(160, 160, 160, 0.2)',
    padding: '16px 0 24px 24px'
  }
};
const TableCell = withStyles(styles)(
  (props) => {
    let wideComponent = false;
    if (props.wide) {
      wideComponent = true;
      delete props.wide;
    }
    const { classes, ...componentProps } = props;
    return (
      <MuiTableCell
        classes={wideComponent ? { root: classes.wideTableCell } : {}}
        {...componentProps}
      />
    );
  }
);

function handleRowClick(pk, href, history) {
  return () => history.push(`${href}/${pk}/`);
}

const Table = (props) => {
  const { headers, data, handlePrev, handleNext, href, history, style, noDataLabel, classes } = props;
  return (
    <div style={style}>
      <MuiTable
        className={classes.childCategory}
      >
        <TableHead>
          <TableRow>
            {headers.map((header) => (
              <TableCell
                wide={header.wide}
                key={header.name}
              >{header.label}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((row) => (
            <TableRow
              onClick={handleRowClick(row.pk, href, history)}
              style={{ cursor: 'pointer' }}
              key={row.id}
            >
              {headers.map((header) => (
                <TableCell
                  wide={header.wide}
                  key={header.name}
                >
                  {row[header.name] ? row[header.name] : header.noDataText}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </MuiTable>
      {!data.length && (
        <div className={classes.noDataText}>
          {noDataLabel}
        </div>
      )}
    </div>
  );
};
Table.propTypes = {
  classes: PropTypes.object,
  headers: PropTypes.array.isRequired,
  handlePrev: PropTypes.func,
  handleNext: PropTypes.func,
  href: PropTypes.string,
  history: PropTypes.object,
  style: PropTypes.object,
  data: PropTypes.array.isRequired,
  noDataLabel: PropTypes.string.isRequired
};

export default withStyles(styles)(withRouter(Table));
