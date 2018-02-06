import React from 'react';
import { withRouter } from 'react-router-dom';
import { withStyles } from 'material-ui/styles';
import Card, { CardContent, CardActions } from 'material-ui/Card';
import Button from 'material-ui/Button';

import { TextField } from '../../components/inputs';

const styles = theme => ({
  cardActions: {
    marginLeft: 0,
    marginRight: 0,
    justifyContent: 'flex-end'
  },
  inputContainer: {
    marginBottom: theme.spacing.unit * 2
  },
  largeTextInput: {
    '& input': {
      fontSize: '2.2rem'
    }
  }
});

function handleBack(history) {
  return () => history.goBack();
}

export default withStyles(styles)(
  withRouter(
    (props) => (
      <Card>
        <CardContent>
          <div className={props.classes.inputContainer}>
            <TextField name={'name'}
              label={'Name'}
              defaultValue={props.category ? props.category.name : ''}
              className={props.classes.largeTextInput}
              required
            />
          </div>
          <div className={props.classes.inputContainer}>
            <TextField name={'description'}
              label={'Description (optional)'}
              defaultValue={props.category ? props.category.description : ''}
              multiline
            />
          </div>
        </CardContent>
        <CardActions classes={{ root: props.classes.cardActions }}>
          <Button color="secondary"
            onClick={handleBack(props.history)}
          >
            Anuluj
          </Button>
          <Button
            variant="raised"
            color="secondary"
            onClick={handleBack(props.history)}
          >
            Aktualizuj
          </Button>
        </CardActions>
      </Card>
    )
  )
);
