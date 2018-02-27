import React from 'react';
import Button from 'material-ui/Button';
import Card, { CardAction, CardContent } from 'material-ui/Card';
import PropTypes from 'prop-types';
import Typography from 'material-ui/Typography';
import { withStyles } from 'material-ui/styles';

import Table from '../table';

const styles = {
  listCard: {
    paddingBottom: 0,
  },
  listCardActions: {
    paddingBottom: 0,
  },
};
const ListCardComponent = (props) => {
  const {
    addActionLabel,
    classes,
    count,
    displayLabel,
    firstCursor,
    handleAddAction,
    handleChangePage,
    handleChangeRowsPerPage,
    headers,
    href,
    label,
    lastCursor,
    list,
    noDataLabel,
    page,
    rowsPerPage,
  } = props;
  return (
    <Card className={classes.listCard}>
      <div>
        {displayLabel && (
          <CardContent className={classes.listCardActions}>
            <Typography variant="display1">
              {label}
            </Typography>
            <Button
              color="secondary"
              onClick={handleAddAction}
              style={{ margin: '2rem 0 1rem' }}
            >
              {addActionLabel}
            </Button>
          </CardContent>
        )}
        <CardContent style={{
          borderTop: 'none',
          padding: 0,
        }}
        >
          <Table
            count={count}
            handleChangePage={handleChangePage(firstCursor, lastCursor)}
            handleChangeRowsPerPage={handleChangeRowsPerPage}
            headers={headers}
            href={href}
            list={list}
            noDataLabel={noDataLabel}
            page={page}
            rowsPerPage={rowsPerPage}
            rowsPerPageOptions={[2, 5, 10]}
          />
        </CardContent>
      </div>
    </Card>
  );
};
ListCardComponent.propTypes = {
  addActionLabel: PropTypes.string,
  classes: PropTypes.object,
  count: PropTypes.number,
  displayLabel: PropTypes.bool,
  firstCursor: PropTypes.string,
  handleAddAction: PropTypes.func,
  handleChangePage: PropTypes.func,
  handleChangeRowsPerPage: PropTypes.func,
  headers: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string,
    label: PropTypes.string,
    wide: PropTypes.bool,
  })),
  href: PropTypes.string,
  label: PropTypes.string,
  lastCursor: PropTypes.string,
  list: PropTypes.array.isRequired,
  noDataLabel: PropTypes.string.isRequired,
  page: PropTypes.number,
  rowsPerPage: PropTypes.number,
};
const ListCard = withStyles(styles)(ListCardComponent);

export {
  ListCard as default,
  ListCardComponent,
};
