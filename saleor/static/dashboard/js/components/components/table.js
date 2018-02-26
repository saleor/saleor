import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import MuiTable, {
  TableHead,
  TableBody,
  TableRow,
  TableCell as MuiTableCell,
  TableFooter,
  TablePagination
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
    padding: '16px 0 24px 24px'
  },
  tableRow: {
    cursor: 'pointer'
  }
};
const TableCell = withStyles(styles)(
  (props) => {
    const { classes, wide, ...componentProps } = props;
    return (
      <MuiTableCell
        classes={wide ? { root: classes.wideTableCell } : {}}
        {...componentProps}
      />
    );
  }
);

function handleRowClick(pk, href, history) {
  return () => history.push(`${href}/${pk}/`);
}

const Table = (props) => {
  const {
    headers,
    list,
    href,
    history,
    className,
    noDataLabel,
    classes,
    rowsPerPage,
    rowsPerPageOptions,
    page,
    count
  } = props;
  return (
    <div className={className}>
      <MuiTable className={classes.childCategory}>
        <TableHead>
          <TableRow>
            {headers.map((header) => (
              <TableCell
                wide={header.wide}
                key={header.name}
              >
                {header.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {list.map((row) => (
            <TableRow
              onClick={handleRowClick(row.id, href, history)}
              className={classes.tableRow}
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
        {list.length > 0 && (
          <TableFooter>
            <TableRow>
              <TablePagination
                colSpan={5}
                count={count}
                rowsPerPage={rowsPerPage}
                rowsPerPageOptions={rowsPerPageOptions || [5, 10, 20]}
                page={page}
                onChangePage={props.handleChangePage}
                onChangeRowsPerPage={props.handleChangeRowsPerPage}
              />
            </TableRow>
          </TableFooter>
        )}
      </MuiTable>
      {!list.length && (
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
  style: PropTypes.string,
  list: PropTypes.array.isRequired,
  noDataLabel: PropTypes.string.isRequired
};

export default withStyles(styles)(withRouter(Table));
