import React, { Fragment } from 'react';
import Button from 'material-ui/Button';
import Modal from 'material-ui/Modal';
import Typography from 'material-ui/Typography';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import { withStyles } from 'material-ui/styles';

const styles = theme => ({
  card: {
    outline: 'none',
    top: '40%',
    left: 'calc(50% - 17rem)',
    position: 'absolute',
    width: '35rem',
  },
  cardActions: {
    margin: 0,
    flexDirection: 'row-reverse',
  },
  title: {
    marginBottom: theme.spacing.unit,
    textTransform: 'uppercase',
  },
  button: {
    marginLeft: theme.spacing.unit / 2,
  },
});
const ConfirmRemoval = withStyles(styles)((props) => {
  const {
    title,
    children,
    classes,
    opened,
    onConfirm,
    onClose,
    ...modalProps
  } = props;
  return (
    <Modal open={opened} {...modalProps}>
      <Card className={classes.card}>
        <CardContent>
          <Typography
            variant="headline"
            className={classes.title}
          >
            {title}
          </Typography>
          <Fragment>
            {children}
          </Fragment>
        </CardContent>
        <CardActions className={classes.cardActions}>
          <Button
            color="secondary"
            variant="raised"
            onClick={onConfirm}
            className={classes.button}
          >
            {pgettext('Dashboard delete action', 'Remove')}
          </Button>
          <Button
            color="secondary"
            onClick={onClose}
            className={classes.button}
          >
            {pgettext('Dashboard cancel action', 'Cancel')}
          </Button>
        </CardActions>
      </Card>
    </Modal>
  );
});

export { ConfirmRemoval };
