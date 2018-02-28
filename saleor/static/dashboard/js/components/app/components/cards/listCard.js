import React from 'react';
import Button from 'material-ui/Button';
import Card, { CardAction, CardContent } from 'material-ui/Card';
import PropTypes from 'prop-types';
import Typography from 'material-ui/Typography';
import { withStyles } from 'material-ui/styles';

import Table from '../table';
import { gettext } from '../../i18n';

const styles = {
  listCard: {
    paddingBottom: 0,
  },
  listCardActions: {
    paddingBottom: 0,
  },
  listCardAddActionButton: {
    margin: '1rem 0',
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
    handleRowClick,
    headers,
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
              className={classes.listCardAddActionButton}
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
            handleRowClick={handleRowClick}
            headers={headers}
            list={list}
            noDataLabel={noDataLabel}
            page={page}
            rowsPerPage={rowsPerPage}
            rowsPerPageOptions={[10, 30, 50]}
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
  handleRowClick: PropTypes.func,
  headers: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string,
    label: PropTypes.string,
    wide: PropTypes.bool,
  })).isRequired,
  label: PropTypes.string,
  lastCursor: PropTypes.string,
  list: PropTypes.array.isRequired,
  noDataLabel: PropTypes.string.isRequired,
  page: PropTypes.number,
  rowsPerPage: PropTypes.number,
};
ListCardComponent.defaultProps = {
  addActionLabel: gettext('Add'),
  displayLabel: false,
};
const ListCard = withStyles(styles)(ListCardComponent);

export {
  ListCard as default,
  ListCardComponent,
};
