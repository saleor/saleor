import React from 'react';
import { withRouter } from 'react-router-dom';
import { withStyles } from 'material-ui/styles';
import Card, { CardContent } from 'material-ui/Card';

import { TextField } from '../../components/inputs';
import { CardActions } from '../../components/cards';
import { FlatButton, RaisedButton } from '../../components/buttons';


const styles = theme => ({
  cardActions: {
    marginLeft: 0,
    marginRight: 0,
    justifyContent: 'flex-end',
  },
  inputContainer: {
    marginBottom: theme.spacing.unit * 2,
  },
  largeTextInput: {
    '& input': {
      fontSize: '2.2rem',
    }
  },
});

function handleBack(history) {
  return (() => history.goBack());
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
                       required />
          </div>
          <div className={props.classes.inputContainer}>
            <TextField name={'description'}
                       label={'Description (optional)'}
                       defaultValue={props.category ? props.category.description : ''}
                       multiline />
          </div>
        </CardContent>
        <CardActions classes={{ root: props.classes.cardActions }}>
          <FlatButton color="secondary"
                      onClick={handleBack(props.history)}>
            Anuluj
          </FlatButton>
          <RaisedButton color="secondary"
                        onClick={handleBack(props.history)}>
            Aktualizuj
          </RaisedButton>
        </CardActions>
      </Card>
    )
  )
);
