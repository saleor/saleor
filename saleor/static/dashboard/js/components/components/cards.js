import React from 'react';
import { Link } from 'react-router-dom';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import Button from 'material-ui/Button';
import { withStyles } from 'material-ui/styles';

import Table from './table';

const styles = (theme) => ({
  cardTitle: {
    fontWeight: 300,
    fontSize: theme.typography.display1.fontSize
  },
  cardSubtitle: {
    fontSize: theme.typography.title.fontSize,
    lineHeight: '110%',
    margin: '0.65rem 0 0.52rem 0'
  },
  listCard: {
    paddingBottom: 0
  },
  listCardActions: {
    paddingBottom: 0
  }
});
const CardTitle = withStyles(styles)(
  (props) => {
    const { classes, children, componentProps } = props;
    return (
      <div className={classes.cardTitle} {...componentProps}>
        {children}
      </div>
    );
  }
);
const CardSubtitle = withStyles(styles)(
  (props) => {
    const { classes, children, componentProps } = props;
    return (
      <div className={classes.cardSubtitle} {...componentProps}>
        {children}
      </div>
    );
  }
);

const DescriptionCard = (props) => {
  const {
    title,
    description,
    editButtonLabel,
    removeButtonLabel,
    editButtonHref,
    handleRemoveButtonClick
  } = props;
  return (
    <div>
      <Card>
        <CardContent>
          <CardTitle>
            {title}
          </CardTitle>
          <CardSubtitle>
            {pgettext('Description card widget description text label', 'Description')}
          </CardSubtitle>
          {description}
          <CardActions>
            <Link to={editButtonHref}>
              <Button color={'secondary'}>
                {editButtonLabel}
              </Button>
            </Link>
            <Button
              color={'secondary'}
              onClick={handleRemoveButtonClick}
            >
              {removeButtonLabel}
            </Button>
          </CardActions>
        </CardContent>
      </Card>
    </div>
  );
};

const ListCardComponent = (props) => {
  const {
    displayLabel,
    headers,
    list,
    firstCursor,
    lastCursor,
    classes,
    handleAddAction,
    handleChangePage,
    handleChangeRowsPerPage,
    page,
    rowsPerPage,
    label,
    addActionLabel,
    noDataLabel
  } = props;
  return (
    <Card className={classes.listCard}>
      <div>
        {displayLabel && (
          <CardContent className={classes.listCardActions}>
            <CardTitle>
              {label}
            </CardTitle>
            <Button
              color={'secondary'}
              style={{ margin: '2rem 0 1rem' }}
              onClick={handleAddAction}
            >
              {addActionLabel}
            </Button>
          </CardContent>
        )}
        <CardContent style={{
          borderTop: props.pk ? '1px solid rgba(160, 160, 160, 0.2)' : 'none',
          padding: 0
        }}>
          <Table
            list={list}
            noDataLabel={noDataLabel}
            headers={headers}
            href="/categories"
            page={page}
            rowsPerPage={rowsPerPage}
            rowsPerPageOptions={[5, 10]}
            count={10}
            handleChangePage={handleChangePage(firstCursor, lastCursor)}
            handleChangeRowsPerPage={handleChangeRowsPerPage}
          />
        </CardContent>
      </div>
    </Card>
  );
};
const ListCard = withStyles(styles)(ListCardComponent);

export {
  CardTitle,
  CardSubtitle,
  DescriptionCard,
  ListCard,
  ListCardComponent
};
