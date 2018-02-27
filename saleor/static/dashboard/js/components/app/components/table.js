import React from 'react';
import MuiTable, {
  TableBody,
  TableCell as MuiTableCell,
  TableFooter,
  TableHead,
  TablePagination,
  TableRow,
} from 'material-ui/Table';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withStyles } from 'material-ui/styles';

const styles = {
  wideTableCell: {
    width: '99%',
  },
  childCategory: {
    tableLayout: 'auto',
  },
  noDataText: {
    marginTop: -8,
    top: 8,
    position: 'relative',
    padding: '16px 0 24px 24px',
  },
  tableRow: {
    cursor: 'pointer',
  },
};
const TableCell = withStyles(styles)((props) => {
  const { classes, wide, ...componentProps } = props;
  return (
    <MuiTableCell
      classes={wide ? { root: classes.wideTableCell } : {}}
      {...componentProps}
    />
  );
});

function handleRowClick(pk, href, history) {
  return () => history.push(`${href}/${pk}/`);
}

const Table = (props) => {
  const {
    className,
    classes,
    count,
    handleChangePage,
    handleChangeRowsPerPage,
    headers,
    history,
    href,
    list,
    noDataLabel,
    page,
    rowsPerPage,
    rowsPerPageOptions,
  } = props;
  return (
    <div className={className}>
      <MuiTable className={classes.childCategory}>
        <TableHead>
          <TableRow>
            {headers.map(header => (
              <TableCell
                key={header.name}
                wide={header.wide}
              >
                {header.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {list.map(row => (
            <TableRow
              className={classes.tableRow}
              key={row.id}
              onClick={handleRowClick(row.id, href, history)}
            >
              {headers.map(header => (
                <TableCell
                  key={header.name}
                  wide={header.wide}
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
                onChangePage={handleChangePage}
                onChangeRowsPerPage={handleChangeRowsPerPage}
                page={page}
                rowsPerPage={rowsPerPage}
                rowsPerPageOptions={rowsPerPageOptions || [5, 10, 20]}
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
  className: PropTypes.string,
  classes: PropTypes.object,
  count: PropTypes.number,
  handleChangePage: PropTypes.func,
  handleChangeRowsPerPage: PropTypes.func,
  headers: PropTypes.array.isRequired,
  history: PropTypes.object,
  href: PropTypes.string,
  list: PropTypes.array.isRequired,
  noDataLabel: PropTypes.string.isRequired,
  style: PropTypes.string,
  page: PropTypes.number,
  rowsPerPage: PropTypes.number,
  rowsPerPageOptions: PropTypes.arrayOf(PropTypes.number),
};

export default withStyles(styles)(withRouter(Table));
