import React from 'react';
import Button from 'material-ui/Button';
import Modal from 'material-ui/Modal';
import Typography from 'material-ui/Typography';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import { withStyles } from 'material-ui/styles';

const styles = {
  card: {
    outline: 'none',
    // height: '11rem',
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
    marginBottom: '1rem',
    textTransform: 'uppercase',
  },
};
const ConfirmRemoval = withStyles(styles)((props) => {
  const { content, classes, ...modalProps } = props;
  return (
    <Modal open={true} {...modalProps}>
      <Card className={classes.card}>
        <CardContent>
          <Typography
            variant="headline"
            className={classes.title}
          >
            Confirm removal
            </Typography>
          <Typography variant="body1">{content}</Typography>
        </CardContent>
        <CardActions className={classes.cardActions}>
          <Button
            color="secondary"
            variant="raised"
            onClick={props.onConfirm}
          >
            Do it!
          </Button>
          <Button
            color="secondary"
            onClick={props.onClose}
          >
            nope
          </Button>
        </CardActions>
      </Card>
    </Modal>
  );
});

export {
  ConfirmRemoval,
};
